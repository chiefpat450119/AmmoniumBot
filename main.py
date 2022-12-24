import praw
from prawcore.exceptions import Forbidden
from praw.exceptions import RedditAPIException
import random
import os

# Script will run every 3 hours


# Get counter from file
def get_counter():
    with open("counter.txt", "r") as file:
        counter = int(file.read())
    return counter


# Update total_runs.txt in case there's no change in counter so no error is thrown
def update_runs():
    with open("total_runs.txt", "r") as file:
        runs = int(file.read())
    runs += 1
    with open("total_runs.txt", "w") as file:
        file.write(str(runs))


# Base mistake class
class Mistake:
    # Constructor function; Parameters for any exceptions, required context and explanations
    def __init__(self, mistake: str, correction: str, exceptions=None, before=" ", after=" ", explanation=None):
        self.mistake = mistake
        self.correction = correction
        self.exceptions = exceptions
        self.before = before
        self.after = after
        self.explanation = explanation

    # Method to check if the comment is an exception
    def is_exception(self, text):
        if not self.exceptions:
            return False
        for exception in self.exceptions:
            return exception in text

    # Method that checks for mistakes in comments and returns relevant corrections
    def check(self, text):
        mistake_string = self.before + self.mistake + self.after
        if mistake_string in text and not self.is_exception(text):
            # Update counter file
            with open("counter.txt", "r") as file:
                counter = int(file.read())
            with open("counter.txt", "w") as file:
                file.write(str(counter + 1))
            return self.correction
        return None

    # Methods that returns the context of the mistake in the comment
    def find_context(self, text):
        mistake_string = self.before + self.mistake + self.after
        # Find the index of the mistake
        index = text.find(mistake_string)
        # Find the index of the first space before the mistake
        first_space = text.rfind(" ", 0, index)
        # Find the index of the first space after the mistake
        second_space = text.find(" ", index + len(mistake_string))
        if first_space == -1:
            first_space = 0
        if second_space == -1:
            second_space = len(text)
        # Return the context
        return text[first_space:second_space]

    # Returns the explanation
    def explain(self):
        if self.explanation:
            return self.explanation
        return "No explanation available."


# There's so many variations of this mistake that I made a subclass for it
class OfMistake(Mistake):
    def __init__(self, mistake, exceptions=None):
        super().__init__(mistake=mistake, correction=mistake + " have", exceptions=exceptions, before=" ", after=" of ")
        self.explanation = "You probably meant to say could've/should've/would've which sounds like 'of' but is actually short for 'have'."
        if not exceptions:
            self.exceptions = ["of course"]


# Likewise for this one (these two are the most irritating as well)
class LooseMistake(Mistake):
    def __init__(self, after, exceptions=None):
        super().__init__(mistake="loose", correction="lose", exceptions=exceptions, before=" ", after=after)
        self.explanation = "Loose is an adjective meaning the opposite of tight, while lose is a verb."


# Reddit API Setup
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
password = os.environ.get("PASSWORD")
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent="console:ammonium_bot:v1.0.0 (by /u/anonymous)",
                     username="ammonium_bot",
                     password=password)

# List of subreddits monitored by the bot
monitored_subreddits = ["memes", "gaming", "videos", "worldnews", "science", "gifs", "clashroyale", "tennis", "showerthoughts", "space", "history", "earthporn", "gadgets", "philosophy", "travel", "philosophy", "femalefashionadvice", "fitness", "oddlysatisfying", "therewasanattempt", "modernwarfareII", "horizon"]


# List of mistake instances that the bot iterates through
mistakes = [
    OfMistake("shouldn't"),
    OfMistake("couldn't"),
    OfMistake("wouldn't"),
    OfMistake("should"),
    OfMistake("would"),
    OfMistake("could"),
    OfMistake("must"),
    OfMistake("might"),
    Mistake("to many", "too many", before=" way "),
    Mistake("to many", "too many", before=" far "),
    Mistake("to little", "too little", before=" way "),
    Mistake("to little", "too little", before=" far "),
    Mistake("to few", "too few", exceptions=["available to few"]),
    Mistake("to much", "too much", exceptions=["open to", "much of", "similar"]),
    Mistake("more then", "more than", exceptions=["any more"]),
    Mistake("less then", "less than", exceptions=["any less"]),
    Mistake("payed", "paid", explanation="Payed means to seal something with wax, while paid means to give money."),
    LooseMistake(" my "),
    LooseMistake(" your "),
    LooseMistake(" his "),
    LooseMistake(" her "),
    LooseMistake(" their "),
    LooseMistake(" our "),
    LooseMistake(" its "),
    Mistake("could care less", "couldn't care less", exceptions=["couldn't care less*", "couldn't*", "did you mean"], explanation="If you could care less, you do care, which is the opposite of what you're trying to say."),
    Mistake("loosing", "losing", explanation="Loose is an adjective meaning the opposite of tight, while lose is a verb."),
    Mistake("looses", "loses", explanation="Loose is an adjective meaning the opposite of tight, while lose is a verb."),
    Mistake("irregardless", "regardless", explanation="irregardless is not a word."),
    Mistake("weary of", "wary of", explanation="Weary means tired, while wary means cautious."),
    Mistake("can't breath", "can't breathe", explanation="Breath is a noun, while breathe is a verb."),
    Mistake("intensive purposes", "intents and purposes", explanation="This is likely due to mishearing of 'intents and purposes'."),
    Mistake("sneak peak", "sneak peek", explanation="peak is the top of a mountain, while peek is a quick look."),
    Mistake("sneak peeks", "sneak peek", explanation="peak is the top of a mountain, while peek is a quick look."),
    Mistake("unphased", "unfazed"),
    Mistake("epitamy", "epitome"),
    Mistake("no affect", "no effect", explanation="affect is a verb meaning to influence, while effect is a noun meaning a result."),
    Mistake("little affect", "little effect", explanation="affect is a verb meaning to influence, while effect is a noun meaning a result."),
    Mistake("peaked my interest", "piqued my interest", explanation="Some people might have peaked in high school, but pique is a verb meaning to arouse interest."),
    Mistake("peaked my curiosity", "piqued my curiosity", explanation="Some people might have peaked in high school, but pique is a verb meaning to arouse interest."),
    Mistake("on accident", "by accident"),
    Mistake("by purpose", "on purpose"),
    Mistake("apart of", "a part of", explanation="apart is an adverb meaning separately, while a part is a noun meaning a portion."),
    Mistake("queue", "cue", after=" the ", explanation="queue is a line, while cue is a signal."),
]


# Makes sure the comment author is not another bot
def is_bot(comment):
    try:
        return "bot" in comment.author.name.lower()
    except AttributeError:
        return True


# Randomly choose a subreddit
subreddit = reddit.subreddit(random.choice(monitored_subreddits))

# Main bot loop
try:
    for submission in subreddit.hot(limit=20):
        if not submission.locked:
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                print(f"Checking comment {comment.id} in {subreddit.display_name}")
                if not comment.saved and not is_bot(comment):
                    for mistake in mistakes:
                        correction = mistake.check(comment.body.lower())

                        if correction:
                            explanation = mistake.explain()
                            context = mistake.find_context(comment.body.lower())
                            comment.reply(body=f"""
> {context}  

Did you mean to say \"{correction}\"?  
Explanation: {explanation}  
Total mistakes found: {get_counter()}  
^^I'm ^^a ^^bot ^^that ^^corrects ^^grammar/spelling ^^mistakes.
^^PM ^^me ^^if ^^I'm ^^wrong ^^or ^^if ^^you ^^have ^^any ^^suggestions.   
^^[Github](https://github.com/chiefpat450119)  
^^[Patron](https://www.patreon.com/chiefpat450119)""")
                            print(f"Corrected a mistake in comment {comment.id} in {subreddit.display_name}")

                            # Save the comment so the bot doesn't reply to it again
                            comment.save()

                            # Stop looping through mistakes if one is found
                            break

    # Automated reply
    for message in reddit.inbox.unread():
        if "good bot" in message.body.lower():
            message.mark_read()
            try:
                message.reply(body="Thank you!")
            except Forbidden:
                pass

        elif "bad bot" in message.body.lower():
            message.mark_read()
            try:
                message.reply(body="Hey, that hurt my feelings :(")
            except Forbidden:
                pass

except RedditAPIException as e:
    print(e)

# Increment total run counter
update_runs()
