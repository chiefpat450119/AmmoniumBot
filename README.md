# Ammonium Bot

### General Information:

Reddit bot built with **Python Reddit API Wrapper (PRAW)**, implementing object-oriented design principles.  
Designed to be unobtrusive and helpful, it corrects common grammatical and etymological mistakes.  
Runs in specified time intervals on GitHub Actions cron job.  
I did my best to avoid the bot triggering when it shouldn't, but if it does, please let me know.  
Feel free to leave suggestions for improvements or new features!

Corrects ~~"should of"~~, ~~"to much"~~, ~~"loosing"~~, and more.

See the project in action [here](https://www.reddit.com/user/ammonium_bot)

### Project Structure:

- `main.py` contains the `AmmoniumBot` class which coordinates the bot's functionality:
    - Holds instances of delegate classes for file management, sending responses, and checking mistakes.
    - Tracks number of mistakes corrected in each run.
    - Manages setup of Reddit API connection and making API calls.
    - Runs main loop to iterate through comments in posts in specified subreddits.
    - Calls methods on delegates for specific tasks.
    - Makes API calls to update subreddit ban-list and reply to messages in inbox.
- `file_manager.py` contains the `FileManager` class which handles file I/O:
    - Reads and writes to `JSON` and `.txt` files for persistent data storage.
    - Manages the list of banned subreddits, list of block-listed users, and `stats.json` file.
- `reply.py` contains the `ReplyManager` class which handles sending replies to comments:
    - Sends replies to comments with identified mistakes.
    - Sends replies to comments with "good bot" or "bad bot".
    - Sends confirmation reply for block-listed users.
- `mistakes.py`
  - Contains `Mistake` and its subclasses which represent grammatical errors.
      - Holds a list of exceptions to the rule which causes the bot to ignore the comment.
          - For example, the bot would usually correct "should of" to "should have", but not if the comment contains "
            should of course".
      - Contains methods to check for the mistake in a comment and correct it.
  - Contains a list of `Mistake` objects which are checked for in comments.
  - Contains `MistakeChecker` class which checks comments for a given list of `Mistake`.

- Stats are available in the `data/stats.json` file, listing the number of "good bot" and "bad bot" comments, as well as the
  number of corrections made.

### What's next:

- Use a database to store persistent data
- Make a webpage for stats?
