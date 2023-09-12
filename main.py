import praw
from prawcore.exceptions import Forbidden, TooManyRequests
from praw.exceptions import RedditAPIException
from reply import send_correction, bot_reply, check_feedback
import os
import random
from mistake_db import mistakes
import json
from time import sleep

# TODO: Implement backoff for rate limits
# Script will run every 3 hours and go through every subreddit in the list


# Update total runs in stats file in case there's no change in mistake counter so no error is thrown
def update_runs():
    with open("stats.json", "r") as file:
        data = json.load(file)
        runs = int(data["total runs"])
    runs += 1
    with open("stats.json", "w") as file:
        data["total runs"] = runs
        json.dump(data, file)


# Reddit API Setup
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
password = os.environ.get("PASSWORD")
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent="console:ammonium:v1.1.0 (by /u/chiefpat450119)",
                     username="ammonium_bot",
                     password=password)

# Detect subreddit bans and add to file
for message in reddit.inbox.unread():
    if "banned from participating" in message.subject.lower():
        message.mark_read()
        # Add to list of banned subreddits
        with open("banned_subs.txt", "a") as file:
            file.write(message.subreddit.display_name.lower() + "\n")


# Read banned subreddits
with open("banned_subs.txt", "r") as file:
    banned_subreddits = file.read().splitlines()


# List of subreddits monitored by the bot
with open("monitored_subs.txt", "r") as file:
    monitored_subreddits = file.read().splitlines()

monitored_subreddits = [subreddit for subreddit in monitored_subreddits if subreddit.lower() not in banned_subreddits]
# Starts from a different subreddit each time in case of ratelimit
random.shuffle(monitored_subreddits)


# Makes sure the comment author is not another bot
def is_bot(comment):
    try:
        return "bot" in comment.author.name.lower()
    except AttributeError:
        return True


# Main bot loop
try:
    # Reply to messages
    for message in reddit.inbox.unread():
        try:
            # Check for STOP command
            if "stop" in message.body.lower():
                message.mark_read()
                # Send a DM
                reddit.redditor(message.author.name).message(subject="Bot Stopped",
                                                             message="You will no longer receive corrections from the bot.")
                # Add user to blocklist
                with open("stopped_users.txt", "a") as f:
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

    # Iterate through subreddits
    for subreddit_name in monitored_subreddits:
        subreddit = reddit.subreddit(subreddit_name)

        # Iterate through submissions in hot
        try:
            for submission in subreddit.hot(limit=20):
                if not submission.locked:  # Check if submission is locked
                    submission.comments.replace_more(limit=None)  # Go through all comments

                    for comment in submission.comments.list():
                        print(f"Checking comment {comment.id} in {subreddit.display_name}")
                        # Check conditions before replying
                        # Check if the user is on the blocklist
                        with open("stopped_users.txt", "r") as f:
                            stopped_users = f.read().splitlines()
                        try:
                            user_stopped = comment.author.name in stopped_users
                        except AttributeError:
                            user_stopped = False

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

                                        print(f"Corrected a mistake in comment {comment.id} in {subreddit.display_name}")

                                    # Skip comment if it's deleted or banned from subreddit
                                    except Forbidden:
                                        continue

                                    # Stop looping through mistakes if one is found
                                    break

        # If subreddit is private, skip it
        except Forbidden:
            continue

        # Catch 429 errors, wait a while and then continue to next subreddit
        except TooManyRequests as e:
            print(e)
            sleep(120)
            continue


# Catch rate limits
except RedditAPIException as e:
    print(e)

# Increment total run counter to prevent empty commit
update_runs()
