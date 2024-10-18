import traceback
import backoff
import praw
import os
import datetime

from praw import models
from prawcore.exceptions import Forbidden, TooManyRequests, NotFound
from praw.exceptions import RedditAPIException
from reply import ReplyManager
from mistakes import MistakeChecker, mistakes
from data_manager import FileManager

# Main bot class
class AmmoniumBot:
	def __init__(self, reply_manager: ReplyManager, file_manager: FileManager, mistake_checker: MistakeChecker):
		self.file_manager = file_manager
		self.reply_manager = reply_manager
		self.mistake_checker = mistake_checker
		self.stopped_users = self.file_manager.get_stopped_users()
		self.praw_instance = AmmoniumBot.get_reddit()
		self.monitored_subreddits = self.file_manager.get_subreddits()
		self.mistakes_found = 0

	def run(self):
		try:
			self.check_inbox()
			self.update_subreddits()
			self.main_loop()
			self.file_manager.update_mistake_counter(self.mistakes_found)

		except RedditAPIException as e:
			print(e)
			raise Exception("Reddit API Exception")
		self.file_manager.update_runs()

	# Main loop iterates through all subreddits
	@backoff.on_exception(backoff.expo, TooManyRequests, max_tries=10, raise_on_giveup=False)
	def main_loop(self) -> None:
		# Iterate through subreddits
		for subreddit_name in self.monitored_subreddits:
			subreddit = self.praw_instance.subreddit(subreddit_name)

			# Check all the posts in the subreddit
			try:
				self.check_posts(subreddit)

			# If subreddit is private, skip it
			except Forbidden:
				continue
			except NotFound:
				continue

	# Check all the posts in a subreddit
	def check_posts(self, subreddit):
		for submission in subreddit.hot(limit=20):
			if submission.saved or submission.locked:
				continue

			print(f"{submission.id} in {subreddit.display_name}")
			submission.comments.replace_more(limit=None)  # Get all comments

			self.check_comments(submission, subreddit.display_name)

			# Save submission (do not revisit) if it is older than a day
			if submission and (datetime.datetime.now(datetime.UTC) - datetime.datetime.fromtimestamp(
				submission.created_utc, datetime.UTC)).days >= 1:
				submission.save()  # Save submission so the bot doesn't check it again
				print(f"Saved submission {submission.id} in {subreddit.display_name}")

	# Check all the comments in a submission
	def check_comments(self, submission: praw.models.Submission, subreddit_name) -> None:
		for comment in submission.comments.list():
			# print(f"{comment.id} in {subreddit_name}")

			# Check conditions before replying
			user_stopped = self.is_stopped(comment)
			if any([AmmoniumBot.is_bot(comment), comment.saved, user_stopped]):
				continue

			# Strip quotes from the comment before checking it
			comment_without_quotes = "\n".join(
				line for line in comment.body.split("\n") if not line.startswith(">")
			).lower()

			detected_mistake = self.mistake_checker.find_mistake(comment_without_quotes)

			if detected_mistake is not None:
				# Save the comment so the bot doesn't reply to it again
				comment.save()

				try:
					self.reply_manager.send_correction(comment=comment,
					                                   text=comment_without_quotes,
					                                   mistake=detected_mistake)

					print(
						f"Corrected a mistake in comment {comment.id} in {subreddit_name}")

				# Skip comment if it's deleted or banned from subreddit
				except Forbidden:
					continue

				self.mistakes_found += 1

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
				self.reply_manager.check_feedback(message, self.file_manager)

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

	# Returns True if the comment is from a bot
	@staticmethod
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
