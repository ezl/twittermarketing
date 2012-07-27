from django.conf import settings
from django.core.management.base import NoArgsCommand

from main.models import TwitterAccount, TwitterAccountSnapshot
from django.contrib.auth.models import User

import utils

class Command(NoArgsCommand):
    help = 'Take snapshots'

    def handle_noargs(self, **options):
        for user in User.objects.all():
            try:
                api = utils.get_user_api(user)
                me = api.me()
            except:
                continue

            twitter_account = TwitterAccount.objects.get(user=user)
            twitter_account_snapshot = TwitterAccountSnapshot(
                twitter_account = twitter_account,
                followers_count = me.followers_count,
                friends_count   = me.friends_count,
                listed_count    = me.listed_count,
                )
            twitter_account_snapshot.save()
            print "saved snapshot for", user


