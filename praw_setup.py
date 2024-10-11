import praw
import os

# Reddit API Setup
def get_reddit():
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    password = os.environ.get("PASSWORD")
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent="console:ammonium:v1.1.0 (by /u/chiefpat450119)",
                         username="ammonium_bot",
                         password=password)
    return reddit