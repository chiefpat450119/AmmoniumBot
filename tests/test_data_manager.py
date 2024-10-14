from unittest import TestCase
from data_manager import FileManager
import json


class TestFileManager(TestCase):
	def setUp(self):
		self.txt_path = "test_files/test.txt"
		self.json_path = "test_files/test.json"
		self.file_manager = FileManager(self.txt_path, self.json_path, self.txt_path, self.json_path, self.txt_path)

	def tearDown(self):
		with open(self.txt_path, "w") as f:
			f.write("")
		with open(self.json_path, "w") as f:
			f.write("{}")

	def test_get_stopped_users(self):
		with open(self.txt_path, "w") as f:
			f.write("user1\nuser2\nuser3")
		self.assertEqual(self.file_manager.get_stopped_users(),
		                 {"user1": True, "user2": True, "user3": True})

	def test_update_runs(self):
		with open(self.json_path, "w") as f:
			f.write('{"total runs": 0}')
		self.file_manager.update_runs()
		with open(self.json_path, "r") as f:
			self.assertEqual(json.load(f), {"total runs": 1})

	def test_update_sub_db(self):
		with open(self.json_path, "w") as f:
			test_dict = {"subreddit": False}
			json.dump(test_dict, f)
		self.file_manager.update_sub_db("subreddit")
		self.file_manager.update_sub_db("subreddit2")
		with open(self.json_path, "r") as f:
			self.assertEqual(json.load(f), {"subreddit": True,
			                                "subreddit2": True})
		with open(self.txt_path, "r") as f:
			self.assertEqual(f.read(), "subreddit\nsubreddit2\n")

	def test_update_sub_db_from_txt(self):
		with open(self.txt_path, "w") as f:
			f.write("subreddit\nsubreddit2")
		self.file_manager.update_sub_db_from_txt()
		with open(self.json_path, "r") as f:
			self.assertEqual(json.load(f), {"subreddit": True,
			                                "subreddit2": True})

	def test_update_mistake_counter(self):
		with open(self.json_path, "w") as f:
			json.dump({"good": 960, "bad": 372, "mistake counter": 25791, "total runs": 3163}, f)
		self.file_manager.update_mistake_counter(3)
		with open(self.json_path, "r") as f:
			self.assertEqual(json.load(f), {"good": 960, "bad": 372, "mistake counter": 25794, "total runs": 3163})
		self.file_manager.update_mistake_counter(2)
		with open(self.json_path, "r") as f:
			self.assertEqual(json.load(f), {"good": 960, "bad": 372, "mistake counter": 25796, "total runs": 3163})

	def test_get_subreddits(self):
		# We need to make the return value a set because the order is randomised
		with open(self.json_path, "w") as f:
			json.dump({"subreddit": False, "subreddit2": True, "subreddit3": False}, f)
		self.assertEqual(set(self.file_manager.get_subreddits()), {"subreddit", "subreddit3"})

		with open(self.json_path, "w") as f:
			json.dump({"subreddit": True, "subreddit2": True, "subreddit3": True}, f)
		self.assertEqual(self.file_manager.get_subreddits(), [])

		with open(self.json_path, "w") as f:
			json.dump({"subreddit": False, "subreddit2": False, "subreddit3": False}, f)
		self.assertEqual(set(self.file_manager.get_subreddits()), {"subreddit", "subreddit2", "subreddit3"})

		with open(self.json_path, "w") as f:
			json.dump({"subreddit": True, "subreddit2": False, "subreddit3": True}, f)
		self.assertEqual(set(self.file_manager.get_subreddits()), {"subreddit2"})

		with open(self.json_path, "w") as f:
			json.dump({"subreddit": False, "subreddit2": True, "subreddit3": False}, f)
		self.assertEqual(set(self.file_manager.get_subreddits()), {"subreddit", "subreddit3"})

	def test_add_to_blocklist(self):
		with open(self.txt_path, "w") as f:
			f.write("user1\nuser2\n")
		self.file_manager.add_to_blocklist("user3")
		with open(self.txt_path, "r") as f:
			self.assertEqual(f.read(), "user1\nuser2\nuser3\n")
