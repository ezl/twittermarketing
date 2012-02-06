import tweepy
from tweepy import TweepError

#rocketleasemia
CONSUMER_KEY = 'zVxVWGT3bIMHrC4th8bJQ'
CONSUMER_SECRET = 'oc8cYDjOwruMJycfoJcfU4CzrnwiMuapfwABm1k4c'

ACCESS_KEY = '478302262-avByTGHc54v3xQnWddte32JEYdFa9TiF5pQZluYA'
ACCESS_SECRET = '9mqnKKS1bzxIN8lPzmOQQRItJqW6amJX2jvVqg8zJ9s'


# ezliu
CONSUMER_KEY = 'zVxVWGT3bIMHrC4th8bJQ'
CONSUMER_SECRET = 'oc8cYDjOwruMJycfoJcfU4CzrnwiMuapfwABm1k4c'

ACCESS_KEY = '86677759-RL0hLMKghY2xDvBQWdVJ8k6Iel951K7jNKHqWgGEJ'
ACCESS_SECRET = 'H5OfM0HhXeR5Pk0eob3Aeg3aPWycIJI2pHF2M87w8I'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

