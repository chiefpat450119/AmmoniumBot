import json

def send_correction(comment, context: str, correction: str, explanation: str):
	comment.reply(body=f"""
> {context}  
    
Did you mean to say \"{correction}\"?  
{explanation}  
[Statistics](https://github.com/chiefpat450119/RedditBot/blob/master/stats.json)  
^^I'm ^^a ^^bot ^^that ^^corrects ^^grammar/spelling ^^mistakes.
^^PM ^^me ^^if ^^I'm ^^wrong ^^or ^^if ^^you ^^have ^^any ^^suggestions.   
^^[Github](https://github.com/chiefpat450119)  
^^Reply ^^STOP ^^to ^^this ^^comment ^^to ^^stop ^^receiving ^^corrections.
""")

def bot_reply(message):
	# Auto reply to bots
	if "bot" in message.author.name.lower():
		message.mark_read()
		message.reply(body="This is the superior bot.")


def check_feedback(message):
	if "good bot" in message.body.lower():  # Auto-reply to good and bad bot comments
		message.mark_read()
		# Increment good/bad bot counter json file
		with open("stats.json", "r") as f:
			data = json.load(f)
		data["good"] += 1
		with open("stats.json", "w") as f:
			json.dump(data, f)

		# Send a reply
		message.reply(body=f"""Thank you!    
		                   Good bot count: {data['good']}  
		                   Bad bot count: {data['bad']}""")

	elif "bad bot" in message.body.lower():
		message.mark_read()
		# Increment good/bad bot counter json file
		with open("stats.json", "r") as f:
			data = json.load(f)
		data["bad"] += 1
		with open("stats.json", "w") as f:
			json.dump(data, f)
		# Send a reply
		message.reply(body=f"""Hey, that hurt my feelings :(  
		                   Good bot count: {data['good']}  
		                   Bad bot count: {data['bad']}""")
