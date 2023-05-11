import json

# TODO: Add a stats link to the bot reply to replace the counter

def send_correction(comment, context: str, correction: str, explanation: str, counter: int):
	comment.reply(body=f"""
> {context}  
    
Did you mean to say \"{correction}\"?  
{explanation}  
Total mistakes found: {counter}  
^^I'm ^^a ^^bot ^^that ^^corrects ^^grammar/spelling ^^mistakes.
^^PM ^^me ^^if ^^I'm ^^wrong ^^or ^^if ^^you ^^have ^^any ^^suggestions.   
^^[Github](https://github.com/chiefpat450119)  
^^Reply ^^STOP ^^to ^^this ^^comment ^^to ^^stop ^^receiving ^^corrections.
""")

def bot_reply(message):
	# Auto reply to bots
	if "bot" in message.author.name.lower():
		message.reply(body="This is the superior bot.")
		message.mark_read()


def check_feedback(message):
	if "good bot" in message.body.lower():  # Auto-reply to good and bad bot comments
		message.mark_read()
		# Increment good/bad bot counter json file
		with open("good_bad_bot.json", "r") as f:
			data = json.load(f)
		data["good"] += 1
		with open("good_bad_bot.json", "w") as f:
			json.dump(data, f)

		# Send a reply
		message.reply(body=f"""Thank you!    
		                   Good bot count: {data['good']}  
		                   Bad bot count: {data['bad']}""")

	elif "bad bot" in message.body.lower():
		message.mark_read()
		# Increment good/bad bot counter json file
		with open("good_bad_bot.json", "r") as f:
			data = json.load(f)
		data["bad"] += 1
		with open("good_bad_bot.json", "w") as f:
			json.dump(data, f)
		# Send a reply
		message.reply(body=f"""Hey, that hurt my feelings :(  
		                   Good bot count: {data['good']}  
		                   Bad bot count: {data['bad']}""")
