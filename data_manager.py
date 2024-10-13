import random
import json


# Loads the list of users who have opted out of the bot
def get_stopped_users() -> dict[str, bool]:
	with open("data/stopped_users.txt", "r") as f:
		users = {user: True for user in f.read().splitlines()}
	return users

def update_runs():
	with open("data/stats.json", "r") as file:
		data = json.load(file)
		runs = int(data["total runs"])
	runs += 1
	with open("data/stats.json", "w") as file:
		data["total runs"] = runs
		json.dump(data, file)

def update_sub_db(subreddit_name: str):
	# Add to list of banned subreddits
	with open("data/banned_subs.txt", "a") as file:
		file.write(subreddit_name + "\n")
	# Update the subreddit database
	with open("data/subreddit_db.json", "r") as file:
		subreddit_dict = json.load(file)
		subreddit_dict[subreddit_name] = True
	with open("data/subreddit_db.json", "w") as file:
		json.dump(subreddit_dict, file)

def update_sub_db_from_txt():
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

