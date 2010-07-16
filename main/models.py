from datetime import datetime, timedelta
from django.db import models


class TwitterUser(models.Model):
    """Users I have added"""
    twitter_id = models.IntegerField()
    screen_name = models.CharField(max_length=100)
    followed_on = models.DateTimeField(auto_now_add=True)
    checked_for_reciprocation = models.BooleanField(default=False)
    following_me = models.BooleanField(default=False)

    def __unicode__(self):
        return self.screen_name

class FollowQueue(models.Model):
    """List of people to follow"""
    screen_name = models.CharField(max_length=100)
