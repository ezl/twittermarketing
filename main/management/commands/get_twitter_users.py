from datetime import datetime, timedelta
import time
import random
from ipshell import ipshell
import pdb

from django.conf import settings
from django.core.management.base import NoArgsCommand
from main.models import TwitterUser, FollowQueue

from tms import api, free_api, reciprocation_window, direct_messages, status_messages, hits_per_query, queries, geocode
from tweepy import TweepError, Cursor

class Command(NoArgsCommand):
    help = 'Find some followers'

    def handle_noargs(self, **options):
        print "* " * 20
        print "Starting cycle: %s" % datetime.now()
        self.me = api.me()
        self.add_untracked_users()
        self.contact_new_followers()
        self.prune_losers()
        self.find_new_followers()
        self.me = api.me()
        print "friends: %s, followers %s" % (self.me.friends_count,
                                             self.me.followers_count)

    def add_untracked_users(self):
        """ Add previously untracked users

            If user is manually followed through the twitter website,
            twittermarketing app doesn't know that a relationship exists.

            This method adds untracked users to our repository so we know
            not to refollow them and we won't multiple message them.
        """

        print "[Check for untracked users]"
        friends_ids = api.friends_ids()
        for friend_id in friends_ids:
            tracked = TwitterUser.objects.filter(twitter_id=friend_id).count()
            if not tracked:
                try:
                    twitter_user = api.get_user(user_id=friend_id)
                except TweepError, e:
                    if twitter_unavailable(e.reason):
                        time.sleep(2)
                    elif busted_rate_limit(e.reason):
                        raise Exception
                    else:
                        print "Error: %s" % e.reason
                else:
                    t = TwitterUser(twitter_id=twitter_user.id,
                                    screen_name=twitter_user.screen_name.lower())
                    t.save()
                    print "  - added previously untracked: %s" % t.screen_name

    def contact_new_followers(self):
        """ Check for new followers

            See if any new people are following us since the last check.
            If so, reach out to them via DM or @reply
        """

        print "[Check for new followers]"
        followers_ids = api.followers_ids(self.me.id)
        new_followers = TwitterUser.objects.filter(twitter_id__in=followers_ids,
                                                     following_me=False)
        print "  - New followers: %s" % new_followers.count()
        # send any new followers a message
        for new_follower in new_followers:
            new_follower.following_me = True
            new_follower.save()
            # don't want to seem to spammy by @username tweeting everyone.
            # send @username spam sparingly, usually send DM
            if random.randint(1, 30) == 10:
                status_message = random.sample(status_messages, 1)[0]
                api.update_status("@%s %s" % (new_follower.screen_name, \
                                              status_message))
                print "    - Updated status to: %s" % new_follower.screen_name
            else:
                direct_message = random.sample(direct_messages, 1)[0]
                api.send_direct_message(user_id=new_follower.twitter_id,
                                        text=direct_message)
                print "    - Sent DM to: %s" % new_follower.screen_name

    def prune_losers(self):
        """Unfollow people who are uninterested in following us.

           When a user is followed by twittermarketing, they are added to a list
           of users we are following.  If after tms.reciprocation_window hours
           have elapsed that user hasn't followed us back, unfollow them to
           make room for more people for us to follow.
        """

        print "[Prune losers]"
        # check to see if people i followed follow me back
        cutoff_time = datetime.now() - timedelta(hours=reciprocation_window)
        unchecked = TwitterUser.objects.filter(checked_for_reciprocation=False,
                                               followed_on__lt=cutoff_time)
        winners = unchecked.filter(following_me=True)
        for w in winners:
            w.checked_for_reciprocation = True
            w.save()
        print "  - Checking %s users for recent follow" % unchecked.count()
        losers = unchecked.filter(following_me=False)
        print "  - Reciprocated follow: %s" % (unchecked.count()-losers.count())
        print "  - Losers: %s" % losers.count()
        for loser in losers:
            loser.checked_for_reciprocation = True
            # those ingrates!
            loser.save()
            try:
                api.destroy_friendship(loser)
            except TweepError, e:
                # probably not friends with them already
                if twitter_unavailable(e.reason):
                    time.sleep(2)
                elif busted_rate_limit(e.reason):
                    raise Exception
                else:
                    print "TweepError: %s: %s" % (loser.screen_name, e)
            else:
                print "defriended that ingrate: %s" % loser

    def find_new_followers(self):
        """Find new followers.

           Using search queries defined in tms.py find new followers.
           Do naive filtering to see if we think they are worth following.
           Make sure we haven't previously followed them.
           Follow anyone who passes through, then add them to our list.
        """

        print "[Find new followers]"
        n = hits_per_query
        search_dict = dict()
        search_dict['lang'] = "en"
        if not geocode is None:
            search_dict['geocode'] = geocode
        statuses = list()
        print "  - query:"
        for q in queries:
            search_dict['q'] = q
            results = [c for c in Cursor(api.search, **search_dict).items(n)]
            print "    - %s: %s hits" % (q, len(results))
            statuses.extend(results)
        # find the likely human candidates
        # people talking to one another. get recipients.
        twitter_usernames = [s.to_user for s in statuses if s.to_user_id]
        # from a likely to be "normal human" source
        twitter_usernames.extend([s.from_user for s in
                                  filter(likely_human, statuses)])
        twitter_usernames = list(set(twitter_usernames))
        twitter_usernames = [u.lower() for u in twitter_usernames]
        # only follow new people
        previously_followed = [i.screen_name for i in
                               TwitterUser.objects.filter(screen_name__in=twitter_usernames)]
        twitter_usernames = filter(lambda x: not x in previously_followed,
                                       twitter_usernames)

        # TODO: store these into a list of followers to follow next time
        # right way to do this is to put everyone in a queue in case too many
        # candidates are received. Then we can follow them on the next cron
        # instead, i'm lazy and arbitrarily chose 120 people to follow
        if len(twitter_usernames) > 120:
            twitter_usernames = twitter_usernames[:120]

        # TODO exhaust the free first, then move to the real.
        # dump to followqueue, add users from followqueue isntead of list
        twitter_users = []
        for u in twitter_usernames:
            try:
                twitter_users.append(api.get_user(u))
            except TweepError, e:
                if twitter_unavailable(e.reason):
                    time.sleep(2)
                elif busted_rate_limit(e.reason):
                    raise Exception
                elif "Not found" in e.reason:
                    print "skipping %s" % u
                else:
                    pass

        print "  - likely human: %s/%s " % (len(twitter_users), n * len(queries))

        # actually start following those dudesicles
        newly_followed = 0
        print "[Start following some dudesicles]"
        for twitter_user in twitter_users:
            try:
                api.create_friendship(twitter_user.id)
            except TweepError, e:
                if twitter_unavailable(e.reason):
                    time.sleep(2)
                elif busted_rate_limit(e.reason):
                    raise Exception
                elif "already on your list" in e.reason:
                    continue
                else:
                    print "Skip %s. TweepError: %s" % (twitter_user.screen_name, e)
                    print "DEBUG THIS. WTF is GOING ON?"
                    # ipshell()
                    continue
            try:
                t = TwitterUser(twitter_id=twitter_user.id,
                                screen_name=twitter_user.screen_name.lower())
                t.save()
                newly_followed += 1
                print "    - Followed: %s" % t.screen_name
            except Exception, e:
                print "Error Saving"
        print "  - Batch followed: %s" % newly_followed
        queue_size = FollowQueue.objects.all().count()
        print "  - Dudesicles waiting to be followed: %s" % queue_size

def likely_human(s):
    good_source_list = [u'web', 'Twitter for iPhone',
                        u'Tweetie for Mac',  u'Twitterrific',
                        u'StockTwits Web', u'StockTwits Desktop',
                        u'StockCharts.com', "Echofon", "Facebook"]
    good_source = s.source in good_source_list
    is_retweet = s.text[:2] == "RT"
    to_someone = s.to_user_id
    return good_source or to_someone or is_retweet

def twitter_unavailable(reason):
    if "status code = 503" in reason:
        print "twitter overloaded"
        return True
    else:
        return False

def busted_rate_limit(reason):
    if "Rate limit exceeded" in reason:
        print "%s rate limit hits remaining " % \
                api.rate_limit_status()["remaining_hits"]
        print "RATE LIMIT EXCEEDED"
        return True
    else:
        return False

