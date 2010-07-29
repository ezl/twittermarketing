import tweepy

CONSUMER_KEY = 'xMGEMdG8sMtE6AY4w2DOQ'
CONSUMER_SECRET = 'tWYRfISLf5khOIlyWw9eArWhf8JiL7YB2eQMd8hfC44'

ACCESS_KEY = '165426141-FONy3up9OtUY1IWDvXfgUjKhHL319AlFKozHCLoI'
ACCESS_SECRET = 'M9UkYWsKaIjT6aTCFvNPIjXo9FBcFy7NQvJiyGPDKo'
ACCESS_KEY = '165426141-FONy3up9OtUY1IWDvXfgUjKhHL319AlFKozHCLoI'
ACCESS_SECRET = 'M9UkYWsKaIjT6aTCFvNPIjXo9FBcFy7NQvJiyGPDKo'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)
free_api = tweepy.API()

direct_messages = ["Hi! I'm buildign http://www.quotesentinel.com/, which sends custom alerts on stocks you follow.  I'd love some feedback.",
                  ]
status_messages = ["Tired of missing opportunities when you're not watching the market?  Quote Sentinel watches for you and sends you alerts!",
                   "Use Quote Sentinel to monitor your investments.  Receive text/email notifications when stocks your watching move.",
                   "Try using Quote Sentinel.  You set price points for your stocks, QS alerts you when the stock trades your price.",
                   "We originally developed this for ourselves to be able to easily monitor stocks. Would love your feedback!",
                   "Get custom stock alerts by SMS using http://www.quotesentinel.com.  Hands down the easiest way to monitor your portfolio!",
                  ]

hits_per_query = 100 # number of statuses to retrieve per query
queries = ["$GOOG", "$AAPL", "$TSLA", "$MSFT", "$GS", "$MS",
           "Berkshire Hathaway", "$XLF", "$INTC", "$CSCO",
          "$SPY",  "$DIA", "$IWM", "$EEM", "$GLD", "$QQQQ", ]

# geocode = "41.877630,-87.624389,35mi" # chicago
geocode = None
