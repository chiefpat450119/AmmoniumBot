import json

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
        exceptions_found = [exception in text for exception in self.exceptions]
        return any(exceptions_found)

    # Method that checks for mistakes in comments and returns relevant corrections
    def check(self, text):
        mistake_string = self.before + self.mistake + self.after
        if mistake_string in text and not self.is_exception(text):
            # Update the counter in stats file
            with open("stats.json", "r") as f:
                data = json.load(f)
            data["mistake counter"] += 1
            with open("stats.json", "w") as f:
                json.dump(data, f)
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
            return f"Explanation: {self.explanation}"
        return ""


# There's so many variations of this mistake that I made a subclass for it
class OfMistake(Mistake):
    def __init__(self, mistake, exceptions=None):
        super().__init__(mistake=mistake, correction=mistake + " have", exceptions=exceptions, before=" ", after=" of ")
        self.explanation = "You probably meant to say could've/should've/would've which sounds like 'of' but is actually short for 'have'."
        if not exceptions:
            self.exceptions = ["of course"]

# Likewise for this one
class LooseMistake(Mistake):
    def __init__(self, after, exceptions=None):
        super().__init__(mistake="loose", correction="lose", exceptions=exceptions, before=" ", after=after)
        self.explanation = "Loose is an adjective meaning the opposite of tight, while lose is a verb."


# List of mistake instances that the bot iterates through
mistakes = [
    OfMistake("shouldn't"),
    OfMistake("couldn't"),
    OfMistake("wouldn't"),
    OfMistake("should"),
    OfMistake("would"),
    OfMistake("could"),
    OfMistake("must"),
    OfMistake("might", exceptions=["the might of", "might of course", "might of the"]),
    Mistake("to many", "too many", before=" way "),
    Mistake("to many", "too many", before=" far "),
    Mistake("to few", "too few", exceptions=["available to few"]),
    Mistake("to much", "too much", before=" way "),
    Mistake("more then", "more than", exceptions=["any more", "some more"],
            explanation="If you didn't mean 'more than' you might have forgotten a comma."),
    Mistake("less then", "less than", exceptions=["any less"],
            explanation="If you didn't mean 'less than' you might have forgotten a comma."),
    Mistake("payed", "paid",
            explanation="Payed means to seal something with wax, "
                        "while paid means to give money."),
    LooseMistake(" my "),
    LooseMistake(" your "),
    LooseMistake(" his "),
    LooseMistake(" her "),
    LooseMistake(" their "),
    LooseMistake(" our "),
    LooseMistake(" its "),
    Mistake("could care less", "couldn't care less",
            exceptions=["couldn't care less*", "couldn't*", "did you mean"],
            explanation="If you could care less, you do care, "
                        "which is the opposite of what you meant to say."),
    Mistake("loosing", "losing",
            explanation="Loose is an adjective meaning the opposite of tight, "
                        "while lose is a verb."),
    Mistake("looses", "loses",
            explanation="Loose is an adjective meaning the opposite of tight, "
                        "while lose is a verb."),
    Mistake("irregardless", "regardless",
            explanation="irregardless is not a word."),
    Mistake("weary of", "wary of", before=" be ",
            explanation="Weary means tired, while wary means cautious."),
    Mistake("can't breath", "can't breathe",
            explanation="Breath is a noun, while breathe is a verb."),
    Mistake("intensive purposes", "intents and purposes",
            explanation="This is likely due to mishearing of 'intents and purposes'."),
    Mistake("sneak peak", "sneak peek",
            explanation="peak is the top of a mountain, while peek is a quick look."),
    Mistake("sneak peaks", "sneak peek",
            explanation="peak is the top of a mountain, while peek is a quick look."),
    Mistake("unphased", "unfazed",
            explanation="Phased means to change, while fazed means to be surprised."),
    Mistake("epitamy", "epitome",
            explanation="Epitamy is not a word."),
    Mistake("no affect", "no effect",
            explanation="affect is a verb meaning to influence, "
                        "while effect is a noun meaning a result."),
    Mistake("little affect", "little effect",
            explanation="affect is a verb meaning to influence, "
                        "while effect is a noun meaning a result."),
    Mistake("peaked my interest", "piqued my interest",
            explanation="Some people might have peaked in high school, "
                        "but pique is a verb meaning to arouse interest."),
    Mistake("peaked my curiosity", "piqued my curiosity",
            explanation="Some people might have peaked in high school, "
                        "but pique is a verb meaning to arouse interest."),
    Mistake("apart of", "a part of",
            explanation="\"apart\" is an adverb meaning separately, "
                        "while \"a part\" is a noun meaning a portion."),
    Mistake("queue", "cue", after=" the ",
            explanation="queue is a line, while cue is a signal."),
    Mistake("humanely possible", "humanly possible",
            explanation="humane means kind, while human means relating to humans."),
    Mistake("intimated by", "intimidated by",
            explanation="intimate means \"closely acquianted\", while intimidate means to frighten."),
    Mistake("per say", "per se",
            explanation="per se is latin for \"by itself\"."),
    Mistake("chocking", "choking",
            explanation="chocking means to block a wheel, while choking means to suffocate."),
]
