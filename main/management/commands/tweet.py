import tweepy
from tweepy import TweepError

CONSUMER_KEY = 'zVxVWGT3bIMHrC4th8bJQ'
CONSUMER_SECRET = 'oc8cYDjOwruMJycfoJcfU4CzrnwiMuapfwABm1k4c'

ACCESS_KEY = '478302262-avByTGHc54v3xQnWddte32JEYdFa9TiF5pQZluYA'
ACCESS_SECRET = '9mqnKKS1bzxIN8lPzmOQQRItJqW6amJX2jvVqg8zJ9s'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

