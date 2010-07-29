import tweepy
 
CONSUMER_KEY = 'xMGEMdG8sMtE6AY4w2DOQ'
CONSUMER_SECRET = 'tWYRfISLf5khOIlyWw9eArWhf8JiL7YB2eQMd8hfC44'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth_url = auth.get_authorization_url()
print 'Please authorize: ' + auth_url
verifier = raw_input('PIN: ').strip()
auth.get_access_token(verifier)
print "ACCESS_KEY = '%s'" % auth.access_token.key
print "ACCESS_SECRET = '%s'" % auth.access_token.secret
