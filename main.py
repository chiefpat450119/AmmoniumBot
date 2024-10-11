import json
import backoff
import praw
from prawcore.exceptions import Forbidden, TooManyRequests, NotFound
from praw.exceptions import RedditAPIException
from reply import send_correction, bot_reply, check_feedback
from mistake_db import mistakes
from praw_setup import get_reddit
from subreddits import get_subreddits, update_subreddits

# Script will run every 3 hours and go through every subreddit in the list
# TODO: Refactor the whole project and make it object-oriented
# TODO: Make it smarter and more time efficient at detecting mistakes

@backoff.on_exception(backoff.expo, TooManyRequests, max_tries=10, raise_on_giveup=False)
def main_loop(reddit: praw.Reddit, subreddits: list[str], ignored_users: dict[str, bool]):
    mistakes_found = 0
    # Iterate through subreddits
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)

        # Iterate through submissions in hot
        try:
            for submission in subreddit.hot(limit=20):
                if not submission.locked:  # Check if submission is locked
                    submission.comments.replace_more(limit=None)  # Go through all comments

                    for comment in submission.comments.list():
                        # print(f"Checking comment {comment.id} in {subreddit.display_name}")

                        # Check conditions before replying
                        user_stopped = is_stopped(comment, ignored_users)

                        # Continue with check if all conditions met
                        if not any([is_bot(comment), comment.saved, user_stopped]):
                            for mistake in mistakes:
                                # Strip quotes from the comment before checking it
                                comment_without_quotes = "\n".join(
                                    line for line in comment.body.split("\n") if not line.startswith(">")
                                ).lower()

                                # Run the check method from the Mistake instance, incrementing the counter
                                correction = mistake.check(comment_without_quotes)

                                if correction:
                                    # Save the comment so the bot doesn't reply to it again
                                    comment.save()

                                    explanation = mistake.explain()
                                    context = mistake.find_context(comment_without_quotes)

                                    try:
                                        send_correction(comment=comment, correction=correction, explanation=explanation,
                                                        context=context)

                                        print(
                                            f"Corrected a mistake in comment {comment.id} in {subreddit.display_name}")

                                    # Skip comment if it's deleted or banned from subreddit
                                    except Forbidden:
                                        continue

                                    mistakes_found += 1

                                    # Stop looping through mistakes if one is found
                                    break

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


def is_stopped(comment, stopped_dict: dict[str, bool]):
    # Check if the user is on the blocklist
    try:
        user_stopped = stopped_dict.get(comment.author.name, False)
    except AttributeError:
        user_stopped = False
    return user_stopped

# Update total runs in stats file in case there's no change in mistake counter so no error is thrown
def update_runs():
    with open("data/stats.json", "r") as file:
        data = json.load(file)
        runs = int(data["total runs"])
    runs += 1
    with open("data/stats.json", "w") as file:
        data["total runs"] = runs
        json.dump(data, file)

# Makes sure the comment author is not another bot
def is_bot(comment):
    try:
        return "bot" in comment.author.name.lower()
    except AttributeError:
        return True

def get_stopped_users():
    with open("data/stopped_users.txt", "r") as f:
        users = {user: True for user in f.read().splitlines()}
    return users

def check_inbox(reddit):
    # Reply to messages
    for message in reddit.inbox.unread():
        # print(message.body.lower())
        try:
            # Check for STOP command
            if "stop" in message.body.lower():
                message.mark_read()
                # Send a DM
                reddit.redditor(message.author.name).message(subject="Bot Stopped",
                                                             message="You will no longer receive corrections from the bot.")
                # Add user to blocklist
                with open("data/stopped_users.txt", "a") as f:
                    f.write(f"{message.author.name}\n")

            # Reply to any bots messages in the inbox
            bot_reply(message)

            # Check for feedback in comments
            check_feedback(message)

        except Forbidden:
            continue
        except AttributeError:
            continue
        except RedditAPIException:
            continue

if __name__ == "__main__":
    # Execute main loop
    try:
        stopped_users = get_stopped_users()
        print(stopped_users)
        praw_instance = get_reddit()
        check_inbox(reddit=praw_instance)
        # Update subreddit list
        update_subreddits(reddit=praw_instance)
        monitored_subreddits = get_subreddits()
        main_loop(reddit=praw_instance, subreddits=monitored_subreddits, ignored_users=stopped_users)
    # Catch rate limits
    except RedditAPIException as e:
        print(e)
        raise Exception("Reddit API Exception")

    # Increment total run counter to prevent empty commit
    update_runs()


