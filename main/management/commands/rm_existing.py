import tweepy
from tweepy import TweepError

CONSUMER_KEY = 'xMGEMdG8sMtE6AY4w2DOQ'
CONSUMER_SECRET = 'tWYRfISLf5khOIlyWw9eArWhf8JiL7YB2eQMd8hfC44'

ACCESS_KEY = '165426141-FONy3up9OtUY1IWDvXfgUjKhHL319AlFKozHCLoI'
ACCESS_SECRET = 'M9UkYWsKaIjT6aTCFvNPIjXo9FBcFy7NQvJiyGPDKo'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

me = api.me()
my_followers = api.followers_ids(me.id)
my_friends = api.friends_ids(me.id)
ingrates = filter(lambda u: u not in my_followers, my_friends)
print me.screen_name
import time

while True:
    print "startloop"
    for n in range(api.rate_limit_status()['remaining_hits']):
        try:
            i = ingrates.pop()
        except:
            raise Exception
        u = api.destroy_friendship(i)
        print "deleted", u.screen_name
    time.sleep(3600)

