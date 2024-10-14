import random
import json

class FileManager:
	def __init__(self, stopped_path, stats_path, banned_subs_path, sub_db_path, monitored_subs_path):
		self.stopped_path = stopped_path
		self.stats_path = stats_path
		self.banned_subs_path = banned_subs_path
		self.monitored_subs_path = monitored_subs_path
		self.sub_db_path = sub_db_path

	def get_stopped_users(self) -> dict[str, bool]:
		with open(self.stopped_path, "r") as f:
			users = {user: True for user in f.read().splitlines()}
		return users

	def update_runs(self):
		with open(self.stats_path, "r") as file:
			data = json.load(file)
			runs = int(data["total runs"])
		runs += 1
		with open(self.stats_path, "w") as file:
			data["total runs"] = runs
			json.dump(data, file)

	def update_sub_db(self, subreddit_name: str):
		# Add to list of banned subreddits
		with open(self.banned_subs_path, "a") as file:
			file.write(subreddit_name + "\n")
		# Update the subreddit database
		with open(self.sub_db_path, "r") as file:
			subreddit_dict = json.load(file)
			subreddit_dict[subreddit_name] = True
		with open(self.sub_db_path, "w") as file:
			json.dump(subreddit_dict, file)

	def update_sub_db_from_txt(self):
		# Update database with using the current text files
		with open(self.banned_subs_path, "r") as file:
			banned_subs = file.read().splitlines()
		with open(self.monitored_subs_path, "r") as file:
			monitored_subs = file.read().splitlines()
		with open(self.sub_db_path, "w") as file:
			subreddit_dict = {sub: sub in banned_subs for sub in monitored_subs}
			json.dump(subreddit_dict, file)

	def update_mistake_counter(self, num_mistakes: int):
		# Update the counter in stats file
		with open(self.stats_path, "r") as f:
			data = json.load(f)
		data["mistake counter"] += num_mistakes
		with open(self.stats_path, "w") as f:
			json.dump(data, f)

	def get_subreddits(self) -> list[str]:
		with open(self.sub_db_path, "r") as file:
			subreddit_dict = json.load(file)
			monitored_subreddits = [sub for sub, banned in subreddit_dict.items() if not banned]
			# Starts from a different subreddit each time in case of ratelimit
			random.shuffle(monitored_subreddits)
		return monitored_subreddits

	def add_to_blocklist(self, username: str):
		with open(self.stopped_path, "a") as f:
			f.write(f"{username}\n")