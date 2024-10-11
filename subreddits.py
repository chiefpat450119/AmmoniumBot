import random
import json

def update_subreddits(reddit):
	# Detect subreddit bans and add to file
	for message in reddit.inbox.all(limit=100):
		if "banned" in message.subject.lower():
			subreddit_name = message.subreddit.display_name.lower()
			message.mark_read()
			# Add to list of banned subreddits
			with open("data/banned_subs.txt", "a") as file:
				file.write(subreddit_name + "\n")
			# Update the subreddit database
			with open("data/subreddit_db.json", "r") as file:
				subreddit_dict = json.load(file)
				subreddit_dict[subreddit_name] = True
			with open("data/subreddit_db.json", "w") as file:
				json.dump(subreddit_dict, file)

def update_from_txt():
	# Update database with using the current text files
	with open("data/banned_subs.txt", "r") as file:
		banned_subs = file.read().splitlines()
	with open("data/monitored_subs.txt", "r") as file:
		monitored_subs = file.read().splitlines()
	with open("data/subreddit_db.json", "w") as file:
		subreddit_dict = {sub: sub in banned_subs for sub in monitored_subs}
		json.dump(subreddit_dict, file)

def get_subreddits() -> list[str]:
	with open("data/subreddit_db.json", "r") as file:
		subreddit_dict = json.load(file)
		monitored_subreddits = [sub for sub, banned in subreddit_dict.items() if not banned]
		# Starts from a different subreddit each time in case of ratelimit
		random.shuffle(monitored_subreddits)
	return monitored_subreddits

