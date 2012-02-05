import tweepy
from tweepy import TweepError, Cursor
import tms
from tms import free_api, reciprocation_window, direct_messages, status_messages, hits_per_query, queries, geocode

from tms import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API()
api = tweepy.API(auth)

queries = [
    "%22looking%20for%20an%20apartment%22",
    "%22running%20credit%20checks%22",
    "%22leasing%20agent%22",
    "%22new%20apartment%22",
    "%22moving%20out%22",
    "%22apartment%20application%22",
    "realtor",
]

def find_new_followers():
    print "[Find new followers]"
    n = hits_per_query
    search_dict = dict()
    search_dict['lang'] = "en"
    if not geocode is None:
        search_dict['geocode'] = geocode
    statuses = list()
    print "  - query:"
    for q in queries:
        search_dict['q'] = q
        results = [c for c in Cursor(api.search, **search_dict).items(n)]
        print "    - %s: %s hits" % (q, len(results))
        statuses.extend(results)
    return statuses

"""
Common operations

-- print the status update from status update object
"@%s: %s" % (t.from_user.ljust(17), t.text)

-- get all parties invovled in these status update
screen_names = [t.to_user for t in superbowl if t.to_user] + [t.from_user for t in superbowl]

api.lookup_users(screen_names=screen_names)

"""

def follow_user(user):
    try:
        api.create_friendship(user.screen_name)
        print "    - Followed: %s" % user.screen_name
    except Exception, e:
        print "Error", e
        return

    try:
        #save the follow?
        #t = TwitterUser(twitter_id=twitter_user.id,
        #                screen_name=twitter_user.screen_name.lower())
        #t.save()
        pass
    except Exception, e:
        print "Error", e

def lookup_users_by_screen_name(screen_names, n=50):
    users = []
    while screen_names:
        chunk, screen_names = screen_names[:n], screen_names[n:]
        try:
            users.extend(api.lookup_users(screen_names=chunk))
        except Exception, e:
            print e
            screen_names = chunk + screen_names
            return users, screen_names
    return users, screen_names


geocode=None
hits_per_query = 5
statuses = find_new_followers()

screen_names = [t.to_user for t in statuses if t.to_user] + [t.from_user for t in statuses]
users, remainder = lookup_users_by_screen_name(screen_names)

for user in users:
    follow_user(user)





