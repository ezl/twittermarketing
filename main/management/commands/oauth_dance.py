import tweepy
 
CONSUMER_KEY = 'zVxVWGT3bIMHrC4th8bJQ'
CONSUMER_SECRET = 'oc8cYDjOwruMJycfoJcfU4CzrnwiMuapfwABm1k4c'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth_url = auth.get_authorization_url()
print 'Please authorize: ' + auth_url
verifier = raw_input('PIN: ').strip()
auth.get_access_token(verifier)
print "ACCESS_KEY = '%s'" % auth.access_token.key
print "ACCESS_SECRET = '%s'" % auth.access_token.secret

ACCESS_KEY = auth.access_token.key
ACCESS_SECRET = auth.access_token.secret

api = tweepy.API(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)


