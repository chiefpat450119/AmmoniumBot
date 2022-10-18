import praw
from praw.exceptions import RedditAPIException
import random
import os

# TODO: Add links for Paypal or Patreon


class Mistake:
    def __init__(self, mistake: str, correction: str, exceptions=None, before=" ", after=" ", explanation=None):
        self.mistake = mistake
        self.correction = correction
        self.exceptions = exceptions
        self.before = before
        self.after = after
        self.explanation = explanation

    def is_exception(self, text):
        if not self.exceptions:
            return False
        for exception in self.exceptions:
            return exception in text

    def check(self, text):
        mistake_string = self.before + self.mistake + self.after
        if mistake_string in text and not self.is_exception(text):
            return self.correction
        return None

    def explain(self):
        if self.explanation:
            return self.explanation
        return "No explanation available."


class OfMistake(Mistake):
    def __init__(self, mistake, exceptions=None):
        super().__init__(mistake=mistake, correction=mistake + " have", exceptions=exceptions, before=" ", after=" of ")
        self.explanation = "You probably meant to say could've/should've/would've which sounds like 'of' but is actually short for 'have'."


class LooseMistake(Mistake):
    def __init__(self, after, exceptions=None):
        super().__init__(mistake="loose", correction="lose", exceptions=exceptions, before=" ", after=after)
        self.explanation = "Loose is an adjective meaning the opposite of tight, while lose is a verb."


client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
password = os.environ.get("PASSWORD")
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent="console:ammonium_bot:v1.0.0 (by /u/chiefpat450119)",
                     username="ammonium_bot",
                     password=password)

monitored_subreddits = ["askreddit", "memes", "dankmemes", "funny", "gaming", "videos", "worldnews", "news", "science", "technology", "gifs", "askscience", "tennis", "showerthoughts"]


mistakes = [
    LooseMistake(" my "),
    LooseMistake(" your "),
    LooseMistake(" his "),
    LooseMistake(" her "),
    LooseMistake(" their "),
    LooseMistake(" our "),
    LooseMistake(" its "),
    OfMistake("shouldn't"),
    OfMistake("couldn't"),
    OfMistake("wouldn't"),
    OfMistake("should"),
    OfMistake("would"),
    OfMistake("could"),
    Mistake("could care less", "couldn't care less", exceptions=["couldn't care less*", "couldn't*", "did you mean"], explanation="If you could care less, you do care, which is the opposite of what you're trying to say."),
    Mistake("loosing", "losing", explanation="Loose is an adjective meaning the opposite of tight, while lose is a verb."),
    Mistake("looses", "loses", explanation="Loose is an adjective meaning the opposite of tight, while lose is a verb."),
    Mistake("alot", "a lot", explanation="alot is not a word."),
    Mistake("irregardless", "regardless", explanation="irregardless is not a word."),
    Mistake("to many", "too many", before="way "),
    Mistake("to many", "too many", before="far "),
    Mistake("to little", "too little", before="way "),
    Mistake("to little", "too little", before="far "),
    Mistake("to few", "too few"),
    Mistake("to much", "too much", exceptions=["much of", "similar"]),
    Mistake("more then", "more than", exceptions=["any more"]),
    Mistake("less then", "less than", exceptions=["any less"]),
    Mistake("payed", "paid", explanation="Payed means to seal something with wax, while paid means to give money."),
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
]


def is_bot(comment):
    try:
        return "bot" in comment.author.name.lower()
    except AttributeError:
        return True


subreddit = reddit.subreddit(random.choice(monitored_subreddits))
try:
    for submission in subreddit.hot(limit=20):
        if not submission.locked:
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                print(f"Checking comment {comment.id}")
                if not comment.saved and not is_bot(comment):
                    for mistake in mistakes:
                        correction = mistake.check(comment.body.lower())

                        if correction:
                            explanation = mistake.explain()
                            comment.reply(body=f"""Did you mean to say \"{correction}\"?  
                                Explanation: {explanation}  
                                ^^I'm ^^a ^^bot ^^that ^^corrects ^^grammar/spelling ^^mistakes.
                                ^^PM ^^me ^^if ^^I'm ^^wrong ^^or ^^if ^^you ^^have ^^any ^^suggestions.   
                                ^^[Github](https://github.com/chiefpat450119)""")
                            print(f"Corrected a mistake in comment {comment.id}")
                            comment.save()
                            break
except RedditAPIException as e:
    print(e)
