import json

import praw
from praw import models

from mistakes import Mistake


class ReplyManager:
	@staticmethod
	def send_correction(comment: praw.models.Comment, text: str, mistake: Mistake):
		context = mistake.find_context(text)
		comment.reply(body=f"""
> {context}  

Hi, did you mean to say \"{mistake.get_correction()}\"?  
{mistake.get_explanation()}  
Sorry if I made a mistake! Please [let me know](https://www.reddit.com/message/compose/?to=chiefpat450119&subject=Bot%20Feedback&message=Your%20feedback%20here) if I did.
Have a great day!  
[Statistics](https://github.com/chiefpat450119/RedditBot/blob/master/stats.json)  
^^I'm ^^a ^^bot ^^that ^^corrects ^^grammar/spelling ^^mistakes.
^^PM ^^me ^^if ^^I'm ^^wrong ^^or ^^if ^^you ^^have ^^any ^^suggestions.   
^^[Github](https://github.com/chiefpat450119)  
^^Reply ^^STOP ^^to ^^this ^^comment ^^to ^^stop ^^receiving ^^corrections.
""")

	# Send reply to bots
	@staticmethod
	def bot_reply(message):
		if "bot" in message.author.name.lower():
			message.mark_read()
			message.reply(body="This is the superior bot.")


	@staticmethod
	def check_feedback(message):
		if "good bot" in message.body.lower():  # Auto-reply to good and bad bot comments
			message.mark_read()
			# Increment good/bad bot counter json file
			with open("data/stats.json", "r") as f:
				data = json.load(f)
			data["good"] += 1
			with open("data/stats.json", "w") as f:
				json.dump(data, f)

			# Send a reply
			message.reply(body=f"""Thank you!    
			                   Good bot count: {data['good']}  
			                   Bad bot count: {data['bad']}""")

		elif "bad bot" in message.body.lower():
			message.mark_read()
			# Increment good/bad bot counter json file
			with open("data/stats.json", "r") as f:
				data = json.load(f)
			data["bad"] += 1
			with open("data/stats.json", "w") as f:
				json.dump(data, f)
			# Send a reply
			message.reply(body=f"""Hey, that hurt my feelings :(  
			                   Good bot count: {data['good']}  
			                   Bad bot count: {data['bad']}""")

	@staticmethod
	def stop_message(user: praw.models.Redditor):
		# Send a DM
		user.message(subject="Bot Stopped",
		             message="You will no longer receive corrections from the bot.")