from datetime import datetime, timedelta
import random
from ipshell import ipshell
import pdb

from django.conf import settings
from django.core.management.base import NoArgsCommand
from main.models import TwitterUser, FollowQueue

from tweet import api
from tweepy import TweepError, Cursor, API

from messages import direct_messages, status_messages

free_api = API()

def likely_human(s):
    good_source_list = [u'web', 'Twitter for iPhone',
                        u'Tweetie for Mac',  u'Twitterrific',
                        u'StockTwits Web', u'StockTwits Desktop',
                        u'StockCharts.com', "Echofon", "Facebook"]
    good_source = s.source in good_source_list
    is_retweet = s.text[:2] == "RT"
    to_someone = s.to_user_id
    return good_source or to_someone or is_retweet

class Command(NoArgsCommand):
    help = 'Find some followers'

    def handle_noargs(self, **options):
        print "* " * 20
        print "Starting cycle: %s" % datetime.now()
        self.me = api.me()
        self.contact_new_followers()
        self.prune_losers()
        self.find_new_followers()

    def contact_new_followers(self):
        # check for new followers
        print "[Check for new followers]"
        my_followers_ids = api.followers_ids(self.me.id)
        new_followers = TwitterUser.objects.filter(twitter_id__in=my_followers_ids,
                                                     following_me=False)
        print "  - New followers: %s" % new_followers.count()
        # send any new followers a message
        for new_follower in new_followers:
            # send @user spam sparingly
            new_follower.following_me = True
            new_follower.save()
            if random.randint(1, 16) == 11:
                status_message = random.sample(status_messages, 1)[0]
                api.update_status("@%s %s" (new_follower.screen_name, status_message))
                print "    - Updated status, message to: %s" % new_follower.screen_name
            else:
                direct_message = random.sample(direct_messages, 1)[0]
                api.send_direct_message(user_id=new_follower.twitter_id, text=direct_message)
                print "    - Sent DM to: %s" % new_follower.screen_name

    def prune_losers(self):
        print "[Prune losers]"
        reciprocation_window = 24 * 3 # hours
        # check to see if people i followed follow me back
        unchecked = TwitterUser.objects.filter(checked_for_reciprocation=False,
                                               followed_on__lt=datetime.now() - timedelta(hours=reciprocation_window))
        print "  - Checking %s users for recent follow" % unchecked.count()
        losers = unchecked.filter(following_me=False)
        print "  - Reciprocated follow: %s" % (unchecked.count() - losers.count())
        print "  - Losers: %s" % losers.count()
        for loser in losers:
            loser.checked_for_reciprocation = True
            loser.save()
            try:
                api.destroy_friendship(loser)
            except TweepError, e:
                print "                                              TweepError: %s: %s" % (loser.screen_name, e)

    def find_new_followers(self):
        print "[Find new followers]"
        queries = ["$GOOG", "$GOOG", "$GOOG", "$GOOG", "$GOOG", "$GOOG", "$GOOG", "$GOOG", "$GOOG", 
                   "$AAPL", "$AAPL", "$AAPL", "$AAPL", "$AAPL", "$AAPL", "$AAPL", "$AAPL", "$AAPL", "$AAPL", 
                   "$MSFT", "$TSLA", "$AOL", "$GS", "$HPQ",]
        q = random.sample(queries, 1)  # query to filter for
        n = 500     # number of statuses to retrieve
        statuses = [c for c in Cursor(api.search, q=q, lang="en").items(n)]

        # find the likely human candidates
        # people talking to one another. get recipients.
        twitter_usernames = [s.to_user for s in statuses if s.to_user_id]
        # bullshit. SearchResult.to_user_id doesn't map to the right user id.
        # http://stackoverflow.com/questions/3256981/tweepy-api-how-to-get-a-users-id-from-a-status-searchresult-object

        # from a likely to be "normal human" source
        twitter_usernames.extend([s.from_user for s in
                                  filter(likely_human, statuses)])
        twitter_usernames = set(twitter_usernames)
        twitter_users = [free_api.get_user(u) for u in twitter_usernames]
        twitter_ids = [u.id for u in twitter_users]
        print "  - query: %s" % q
        print "  - probable human: %s / %s " % (len(twitter_ids), n)

        # TODO: filter by location order.  this is sloppy.

        # filter by location
        filter_by_location = None
        chi_geocode = "41.877630,-87.624389,35mi"
        if filter_by_location is not None:
            print "filtering by location"

            local_users = [u for u in twitter_users \
                           if filter_by_location.lower() in u.location.lower()]

        # only follow new people
        previously_followed = [i.twitter_id for i in
                  TwitterUser.objects.filter(twitter_id__in=twitter_ids)]
        new_twitter_ids = filter(lambda x: not x in previously_followed, twitter_ids)
        print "  - new humans: %s" % (len(new_twitter_ids), n)
        newly_followed = 0
        for twitter_id in new_twitter_ids:
            try:
                api.create_friendship(twitter_id)
            except TweepError, e:
                print "                                    Skipping. TweepError: %s: %s" % (twitter_id, e)
            else:
                t = TwitterUser(twitter_id=twitter_id)
                try:
                    t.screen_name = api.get_user(user_id=twitter_id).screen_name
                    t.save()
                    newly_followed += 1
                    print "    - Followed: %s" % t.screen_name
                except Exception, e:
                    print "Error Saving"
        print "  - [Batch followed: %s]" % newly_followed

