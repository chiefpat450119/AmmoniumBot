from prawcore.exceptions import Forbidden, TooManyRequests, NotFound
from praw.exceptions import RedditAPIException
from reply import send_correction, bot_reply, check_feedback
from mistake_db import mistakes
import json
import backoff
from praw_setup import get_reddit
from subreddits import get_subreddits, update_subreddits

# Script will run every 3 hours and go through every subreddit in the list


# Update total runs in stats file in case there's no change in mistake counter so no error is thrown
def update_runs():
    with open("data/stats.json", "r") as file:
        data = json.load(file)
        runs = int(data["total runs"])
    runs += 1
    with open("data/stats.json", "w") as file:
        data["total runs"] = runs
        json.dump(data, file)

monitored_subreddits = []

# Makes sure the comment author is not another bot
def is_bot(comment):
    try:
        return "bot" in comment.author.name.lower()
    except AttributeError:
        return True

@backoff.on_exception(backoff.expo, TooManyRequests, max_tries=10, raise_on_giveup=False)
def main_loop(reddit):
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

    # Iterate through subreddits
    for subreddit_name in monitored_subreddits:
        subreddit = reddit.subreddit(subreddit_name)

        # Iterate through submissions in hot
        try:
            for submission in subreddit.hot(limit=20):
                if not submission.locked:  # Check if submission is locked
                    submission.comments.replace_more(limit=None)  # Go through all comments

                    for comment in submission.comments.list():
                        # print(f"Checking comment {comment.id} in {subreddit.display_name}")

                        # Check conditions before replying
                        # TODO: Refactor this into a separate function
                        # Check if the user is on the blocklist
                        with open("data/stopped_users.txt", "r") as f:
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

                                        print(
                                            f"Corrected a mistake in comment {comment.id} in {subreddit.display_name}")

                                    # Skip comment if it's deleted or banned from subreddit
                                    except Forbidden:
                                        continue

                                    # Stop looping through mistakes if one is found
                                    break

        # If subreddit is private, skip it
        except Forbidden:
            continue
        except NotFound:
            continue

if __name__ == "__main__":
    # Execute main loop
    try:
        # Update subreddit list
        update_subreddits(reddit=get_reddit())
        monitored_subreddits = get_subreddits()
        main_loop(reddit=get_reddit())
    # Catch rate limits
    except RedditAPIException as e:
        print(e)

    # Increment total run counter to prevent empty commit
    update_runs()


