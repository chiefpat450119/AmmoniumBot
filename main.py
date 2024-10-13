import json
import backoff
import praw
import os
from prawcore.exceptions import Forbidden, TooManyRequests, NotFound
from praw.exceptions import RedditAPIException
from reply import ReplyManager
from mistakes import mistakes, MistakeChecker
from data_manager import get_subreddits, update_sub_db, get_stopped_users, update_runs

# Script will run every 6 hours and go through every subreddit in the list
# TODO: Make it smarter and more time efficient at detecting mistakes

class AmmoniumBot:
    def __init__(self):
        self.stopped_users = get_stopped_users()
        self.praw_instance = AmmoniumBot.get_reddit()
        self.monitored_subreddits = get_subreddits()
        self.reply_manager = ReplyManager()
        self.mistake_checker = MistakeChecker()

    def run(self):
        try:
            self.check_inbox()
            self.update_subreddits()
            self.main_loop()
        except RedditAPIException as e:
            print(e)
            raise Exception("Reddit API Exception")
        update_runs()

    @backoff.on_exception(backoff.expo, TooManyRequests, max_tries=10, raise_on_giveup=False)
    def main_loop(self):
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
                        # print(f"Saved submission {submission.id} in {subreddit.display_name}")

            # If subreddit is private, skip it
            except Forbidden:
                continue
            except NotFound:
                continue



        # Update the counter in stats file
        with open("data/stats.json", "r") as f:
            data = json.load(f)
        data["mistake counter"] += mistakes_found
        with open("data/stats.json", "w") as f:
            json.dump(data, f)

    def is_stopped(self, comment: praw.Reddit.comment) -> bool:
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
                    self.praw_instance.redditor(message.author.name).message(subject="Bot Stopped",
                                                                 message="You will no longer receive corrections from the bot.")
                    # Add user to blocklist
                    with open("data/stopped_users.txt", "a") as f:
                        f.write(f"{message.author.name}\n")

                # Reply to any bots messages in the inbox
                self.reply_manager.bot_reply(message)

                # Check for feedback in comments
                self.reply_manager.check_feedback(message)

            except Forbidden:
                continue
            except AttributeError:
                continue
            except RedditAPIException:
                continue

    def update_subreddits(self):
        # Detect subreddit bans and add to file
        for message in self.praw_instance.inbox.all(limit=100):
            if "banned" in message.subject.lower():
                subreddit_name = message.subreddit.display_name.lower()
                message.mark_read()
                update_sub_db(subreddit_name)


    @staticmethod
    # Makes sure the comment author is not another bot
    def is_bot(comment: praw.Reddit.comment):
        try:
            return "bot" in comment.author.name.lower()
        except AttributeError:
            return True

    # Reddit API Setup
    @staticmethod
    def get_reddit():
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
    bot = AmmoniumBot()
    bot.run()