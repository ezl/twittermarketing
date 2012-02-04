import tweepy

CONSUMER_KEY = 'zVxVWGT3bIMHrC4th8bJQ'
CONSUMER_SECRET = 'oc8cYDjOwruMJycfoJcfU4CzrnwiMuapfwABm1k4c'

ACCESS_KEY = '478302262-avByTGHc54v3xQnWddte32JEYdFa9TiF5pQZluYA'
ACCESS_SECRET = '9mqnKKS1bzxIN8lPzmOQQRItJqW6amJX2jvVqg8zJ9s'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)
free_api = tweepy.API()

reciprocation_window = 24 * 2 # hours
direct_messages = ["I'd love some feedback.",
                  ]
status_messages = ["Hello World",
                   "Hello world",
                   "Hello world",
                   "Hello world",
                  ]

hits_per_query = 100 # number of statuses to retrieve per query
queries = ["i had sex last night",
          "find an apartment",
          "need to find a tenant",
          "hate paper applications",
          "run a credit check",]

# geocode = "41.877630,-87.624389,35mi" # chicago
geocode = None
geocode = "25.774252,-80.190262,35mi"
