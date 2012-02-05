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


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User)


class TwitterAccount(TimeStampedModel):
    user = models.ForeignKey(User)
    screen_name     = models.CharField(max_length=255, null=True, blank=True)
    name            = models.CharField(max_length=255, null=True, blank=True)
    twitter_id      = models.CharField(max_length=255, null=True, blank=True)
    location        = models.CharField(max_length=255, null=True, blank=True)
    description     = models.CharField(max_length=255, null=True, blank=True)
    url             = models.CharField(max_length=255, null=True, blank=True)
    followers_count = models.CharField(max_length=255, null=True, blank=True)
    friends_count   = models.CharField(max_length=255, null=True, blank=True)
    listed_count    = models.CharField(max_length=255, null=True, blank=True)


def create_user_profile_on_user_post_save(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)

signals.post_save.connect(
    create_user_profile_on_user_post_save,
    sender=User)
