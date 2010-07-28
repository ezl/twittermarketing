import tweepy
 
CONSUMER_KEY = 'GLwd7ASEFfRXHYuHAERg'
CONSUMER_SECRET = '0jcGweCrkzCywLlLFZGoJmRBYU2iYlvhGgnaiA4'

ACCESS_KEY = '94199104-6uY8cydtbFY9Np6R8VJifQd63N1q1J2JvsOGg9k8'
ACCESS_SECRET = 'a7egUjduQ9U05v2nZu954YLXTmos51Y4qfwavhLdKM'
 
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)
free_api = tweepy.API()

# https://spreadsheets.google.com/ccc?key=0Atiu96hq4WEEdHBsdjlUUngxZV9TcV9uaTU3ZkV5YVE&hl=en&pli=1

direct_messages = ["Check out http://spaciety.com for all of your Chicago Spa booking needs!",
                  ]
status_messages = ["http://spaciety.com has more massage deals than ever today!",
                  ]

hits_per_query = 10 # number of statuses to retrieve per query

queries = ['prenatal massage',
           'hot stone massage',
           'aromatherapy massage',
           'gold coast massage',
           'sports massage',
           'deep tissue massage',
           'swedish massage',
          ]

geocode = "41.877630,-87.624389,35mi" # chicago
# geocode = None
