from main.models import TwitterAccount
from django.db import models
from django.conf import settings
import tweepy

def get_user_api(user):
    if user.is_authenticated():
        auth = tweepy.OAuthHandler(settings.CONSUMER_KEY,
                                   settings.CONSUMER_SECRET)
        auth.set_access_token(user.twitteraccount.access_key,
                              user.twitteraccount.access_secret)
        api = tweepy.API(auth)
    else:
        api = tweepy.API()
    return api

def get_or_create_twitter_account(tweepy_user):
    """get or create an internal TwitterAccount object

       from a tweepy user
    """
    screen_name = tweepy_user.screen_name.lower()

    # Oops! This is a mistake... this should be the SAME. uniqueness of name isn't enforced
    # at the model level... so this is fucked up somehow.
    # putting a bandaid on this in this method because the get() screws up if multiple objects
    # are returned, but one day...
    # In [9]: TwitterAccount.objects.all().count()
    # Out[9]: 1332484
    # In [10]: TwitterAccount.objects.all().distinct().count()
    # Out[10]: 1332490

    # get the account, or create it if we don't know this person
    try:
        twitter_account, created = TwitterAccount.objects.get_or_create(
            screen_name = screen_name
            )
    except TwitterAccount.MultipleObjectsReturned:
        twitter_account = TwitterAccount.objects.filter(screen_name=screen_name).order_by("created")[0]
        created = False
    # if its freshly created, add more info and save it
    if created:
        twitter_account.name          = tweepy_user.name
        twitter_account.twitter_id    = tweepy_user.id
        twitter_account.location      = tweepy_user.location
        twitter_account.description   = tweepy_user.description
        twitter_account.url           = tweepy_user.url
        twitter_account.save()
    return twitter_account, created

def lookup_users_by_screen_name(api, screen_names, n=50):
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

def lookup_users_by_id(api, ids, n=50):
    screen_names = ids
    users = []
    while screen_names:
        chunk, screen_names = screen_names[:n], screen_names[n:]
        try:
            users.extend(api.lookup_users(user_ids=chunk))
        except Exception, e:
            print e
            screen_names = chunk + screen_names
            return users, screen_names
    return users, screen_names

