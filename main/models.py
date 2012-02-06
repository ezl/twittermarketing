from datetime import datetime, timedelta
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import User
from django.db.models import signals


class TwitterUser(TimeStampedModel):
    """Users I have added"""
    twitter_id = models.IntegerField()
    screen_name = models.CharField(max_length=100)
    followed_on = models.DateTimeField(auto_now_add=True)
    checked_for_reciprocation = models.BooleanField(default=False)
    following_me = models.BooleanField(default=False)

    def __unicode__(self):
        return self.screen_name


class FollowQueue(TimeStampedModel):
    """List of people to follow"""
    screen_name = models.CharField(max_length=100)


# NEW STUFF BELOW HERE!

class UserProfile(TimeStampedModel):
    TWEET  = "T"
    FOLLOW = "F"
    STRATEGY_CHOICES = (
        (TWEET,  "Send tweets to all candidates."),
        (FOLLOW, "Follow candidates"),
    )
    user = models.OneToOneField(User)
    marketing_on = models.BooleanField(default=False, help_text="This is OFF by default.  If you put it ON, the site will search for twitter users for you and try to engage them")
    strategy = models.CharField(max_length=1, choices=STRATEGY_CHOICES, default=FOLLOW, help_text="Only the 'follow candidates' strategy does anything for now")
    reciprocation_window = models.IntegerField(default=72)
    geocode = models.CharField(max_length=63, null=True, blank=True, help_text="set up the geocode as per twitters examples on their dveloper homepage.  they look like 'latitude,longitude,radius'.  Example for Miami: '25.774252,-80.190262,35mi'")
    hits_per_query = models.IntegerField(default=50)
    query_help_text = (
        "Each row specifies a query to run on Twitter. This is equivalent to "
        "searching for tweets on http://twitter.com/search. "
        "However, be aware that there are weird formatting issues."
        "Read https://dev.twitter.com/docs/using-search to understand how "
        "to construct your queries."
    )
    queries = models.TextField(help_text=query_help_text, null=True, blank=True)



class TwitterAccount(TimeStampedModel):
    user            = models.OneToOneField(User, null=True, blank=True)
    screen_name     = models.CharField(max_length=255, null=True, blank=True)
    name            = models.CharField(max_length=255, null=True, blank=True)
    twitter_id      = models.CharField(max_length=255, null=True, blank=True)
    location        = models.CharField(max_length=255, null=True, blank=True)
    description     = models.CharField(max_length=255, null=True, blank=True)
    url             = models.CharField(max_length=255, null=True, blank=True)

    access_key      = models.CharField(max_length=255, null=True, blank=True)
    access_secret   = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.screen_name

class TwitterAccountSnapshot(TimeStampedModel):
    twitter_account = models.ForeignKey(TwitterAccount)
    followers_count = models.CharField(max_length=15, null=True, blank=True)
    friends_count   = models.CharField(max_length=15, null=True, blank=True)
    listed_count    = models.CharField(max_length=15, null=True, blank=True)


class Target(TimeStampedModel):
    """These are twitter users that the user has targeted at some point.
       We keep track of this so we don't repeatedly spam people.
       There are 2 basic strategies:
           1. follow people
           2. tweet at people

       Following people requires that we maintain several states to so we
       can unfollow them later, otherwise the game will end as soon as we
       hit 2000 followers.  The "purgatory/follower/ingrate" states refer to
       this.  The "Contacted" state is used if we're implementing the strategy
       of tweeting at targets, so we'll only tweet/dm them once each.

       On deck means we haven't yet initiated any contact with them.
    """
    ON_DECK   = "Q"
    PURGATORY = "P"
    FOLLOWER  = "F"
    INGRATE   = "I"
    CONTACTED = "C"

    STATUS_CHOICES = (
        (ON_DECK,  "User is in the queue to be targeted"),
        (PURGATORY,"User has been followed by us, now waiting to see if the follow us back"),
        (FOLLOWER, "User reciprocated follow"),
        (INGRATE,  "User sucks. We followed them and they didn't follow us. Ingrate!"),
        (CONTACTED,"We contacted this user by @replying or DMing them."),
    )

    hunter = models.ForeignKey(User)
    hunted = models.ForeignKey(TwitterAccount)
    reason = models.CharField(max_length=255, help_text="Why did we target this user?")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=ON_DECK)


def create_user_profile_on_user_post_save(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)

signals.post_save.connect(
    create_user_profile_on_user_post_save,
    sender=User)
