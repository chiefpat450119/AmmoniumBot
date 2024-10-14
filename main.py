import traceback

import backoff
import praw
import os

from praw import models
from prawcore.exceptions import Forbidden, TooManyRequests, NotFound
from praw.exceptions import RedditAPIException
from reply import ReplyManager
from mistakes import MistakeChecker, mistakes
from data_manager import FileManager

# Script will run every 6 hours and go through every subreddit in the list

class AmmoniumBot:
    def __init__(self, reply_manager: ReplyManager, file_manager: FileManager, mistake_checker: MistakeChecker):
        self.file_manager = file_manager
        self.reply_manager = reply_manager
        self.mistake_checker = mistake_checker
        self.stopped_users = self.file_manager.get_stopped_users()
        self.praw_instance = AmmoniumBot.get_reddit()
        self.monitored_subreddits = self.file_manager.get_subreddits()


    def run(self):
        try:
            self.check_inbox()
            self.update_subreddits()
            num_mistakes: int = self.main_loop()
            self.file_manager.update_mistake_counter(num_mistakes)

        except RedditAPIException as e:
            print(e)
            raise Exception("Reddit API Exception")
        self.file_manager.update_runs()

    # Main loop that goes through all the subreddits and comments, return number of mistakes found
    @backoff.on_exception(backoff.expo, TooManyRequests, max_tries=10, raise_on_giveup=False)
    def main_loop(self) -> int:
        mistakes_found = 0
        # Iterate through subreddits
        for subreddit_name in self.monitored_subreddits:
            subreddit = self.praw_instance.subreddit(subreddit_name)

            # Iterate through submissions in hot
            try:
                for submission in subreddit.hot(limit=20):
                    if not submission.saved and not submission.locked:  # Check if submission is saved or locked
                        submission.comments.replace_more(limit=None)  # Get all comments

                        # Loop through comments in submission
                        for comment in submission.comments.list():
                            # print(f"{comment.id} in {subreddit.display_name}")

                            # Check conditions before replying
                            user_stopped = self.is_stopped(comment)

                            # Continue with check if all conditions met
                            if not any([AmmoniumBot.is_bot(comment), comment.saved, user_stopped]):
                                # Strip quotes from the comment before checking it
                                comment_without_quotes = "\n".join(
                                    line for line in comment.body.split("\n") if not line.startswith(">")
                                ).lower()

                                detected_mistake = self.mistake_checker.find_mistake(comment_without_quotes)

                                if detected_mistake:
                                    # Save the comment so the bot doesn't reply to it again
                                    comment.save()

                                    try:
                                        self.reply_manager.send_correction(comment=comment,
                                                                           text = comment_without_quotes,
                                                                           mistake = detected_mistake)

                                        print(
                                            f"Corrected a mistake in comment {comment.id} in {subreddit.display_name}")

                                    # Skip comment if it's deleted or banned from subreddit
                                    except Forbidden:
                                        continue

                                    mistakes_found += 1

                        submission.save()  # Save submission so the bot doesn't check it again
                        print(f"Saved submission {submission.id} in {subreddit.display_name}")

            # If subreddit is private, skip it
            except Forbidden:
                continue
            except NotFound:
                continue


        return mistakes_found

    def is_stopped(self, comment: praw.models.Comment) -> bool:
        # Check if the user is on the blocklist
        try:
            user_stopped = self.stopped_users.get(comment.author.name, False)
        except AttributeError:
            user_stopped = False
        return user_stopped

    def check_inbox(self):
        # Reply to messages
        for message in self.praw_instance.inbox.unread():
            # print(message.body.lower())
            try:
                # Check for STOP command
                if "stop" in message.body.lower():
                    message.mark_read()
                    # Send a DM
                    user: praw.models.Redditor = self.praw_instance.redditor(message.author.name)
                    self.reply_manager.stop_message(user)
                    # Add user to blocklist
                    self.file_manager.add_to_blocklist(message.author.name)

                # Reply to any bots messages in the inbox
                self.reply_manager.bot_reply(message)

                # Check for feedback in comments
                self.reply_manager.check_feedback(message)

            except Forbidden:
                traceback.print_exc()
                continue
            except AttributeError:
                traceback.print_exc()
                continue
            except RedditAPIException:
                traceback.print_exc()
                continue

    def update_subreddits(self):
        # Detect subreddit bans and add to file
        for message in self.praw_instance.inbox.all(limit=100):
            if "banned" in message.subject.lower():
                subreddit_name: str = message.subreddit.display_name.lower()
                message.mark_read()
                self.file_manager.update_sub_db(subreddit_name)


    @staticmethod
    # Makes sure the comment author is not another bot
    def is_bot(comment: praw.models.Comment) -> bool:
        try:
            return "bot" in comment.author.name.lower()
        except AttributeError:
            return True

    # Reddit API Setup
    @staticmethod
    def get_reddit() -> praw.Reddit:
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECRET")
        password = os.environ.get("PASSWORD")
        reddit = praw.Reddit(client_id=client_id,
                             client_secret=client_secret,
                             user_agent="console:ammonium:v1.1.0 (by /u/chiefpat450119)",
                             username="ammonium_bot",
                             password=password)
        return reddit

if __name__ == "__main__":
    rm = ReplyManager()
    fm = FileManager("data/stopped_users.txt",
                     "data/stats.json",
                     "data/banned_subs.txt",
                     "data/subreddit_db.json",
                     "data/monitored_subs.txt")
    mc = MistakeChecker(mistakes)
    bot = AmmoniumBot(rm, fm, mc)
    bot.run()