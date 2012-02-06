from datetime import datetime, timedelta
import time
import random

from django.conf import settings
from django.core.management.base import NoArgsCommand

from main.models import TwitterAccount, Target, UserProfile
from django.contrib.auth.models import User

import utils
import tweepy
from tweepy import TweepError, Cursor

from utils import lookup_users_by_id, lookup_users_by_screen_name

# add new followers # assume these were hand added, so they are "good", can skip purgatory (set them to FOLLOWER)
# add new followees # woot! new people following us! 2 types:
#                          1) purgatory as a funnel -- we message them
#                          2) people just love us -- skip purgatory also (set them to FOLLOWER)
# prune losers.  if they're over the period, set them into the loser category
# start hunting for new people. as we find them, add them to the db
# pop people off the list until we hit the limit.
"""
Common operations

-- print the status update from status update object
"@%s: %s" % (t.from_user.ljust(17), t.text)

-- get all parties invovled in these status update
screen_names = [t.to_user for t in superbowl if t.to_user] + [t.from_user for t in superbowl]

api.lookup_users(screen_names=screen_names)

"""

queries = [
    "%22looking%20for%20an%20apartment%22",
    #"%22running%20credit%20checks%22",
    #"%22leasing%20agent%22",
    #"%22new%20apartment%22",
    #"%22moving%20out%22",
    "%22apartment%20application%22",
    #"realtor",
]


class Command(NoArgsCommand):
    help = 'Find some followers'

    def handle_noargs(self, **options):
        profiles = UserProfile.objects.filter(marketing_on=True)
        print "=" * 70
        print "[ Start marketing ]".center(70)
        print "=" * 70
        for profile in profiles:
            # get the user
            user = profile.user

            # get the params of the marketing strategy
            geocode = profile.geocode.strip() or None
            hits_per_query = profile.hits_per_query
            reciprocation_window = profile.reciprocation_window
            queries = [q.strip() for q in profile.queries.split("\r\n")]
            strategy = profile.strategy

            api = utils.get_user_api(user)
            print "[ Start marketing for %s ]" % user
            self.api = api
            self.user = user
            self.me = api.me()
            print "friends: %s, followers %s" % (self.me.friends_count,
                                                 self.me.followers_count)
            # Do work

            # DB consistency operations -- make sure our sheets match twitter sheets.  we track adds, not deletes.
            # This takes a long time, we can move it to its own function later to run daily instead of hourly
            self.add_untracked_friends()
            self.add_untracked_followers()

            #main work
            self.prune_losers()
            self.find_new_followers()
            self.initiate_contact()


    def add_untracked_friends(self):
        """ Add previously untracked users

            If user is manually followed through the twitter website,
            twittermarketing app doesn't know that a relationship exists.

            This method adds untracked users to our repository so we know
            not to refollow them and we won't multiple message them.
        """

        print "[Check for untracked friends]"
        friends_ids_api = self.api.friends_ids()[0]
        friends_ids_django = [t.hunted.twitter_id for t in Target.objects\
                .filter(hunter=self.user)\
                .exclude(status__in=Target.ON_DECK)
            ]
        untracked_friends_ids = filter(lambda x: unicode(x) not in friends_ids_django,
                                       friends_ids_api)

        untracked_friends, remainder = lookup_users_by_id(self.api, untracked_friends_ids)
        for untracked_friend in untracked_friends:
            twitter_account, created = utils.get_or_create_twitter_account(untracked_friend)
            target, created = Target.objects.get_or_create(
                hunter = self.user,
                hunted = twitter_account,
                )
            target.reason = "External add."
            target.status = Target.FOLLOWER
            target.save()
            print "  - add friend: %s" % \
                    twitter_account.screen_name

    def add_untracked_followers(self):
        """ Add previously untracked users

            These are people that are following us, but the django
            database doesn't know about. What that means is that they
            started following us since the last run of this function.
            There are 2 reasons that happens:
                1) We followed them, then they started following us
                2) They randomly decided to start following us or we
                   tweeted at them and they started following us.

            In case 1, that means we had initially put them into purgatory and
            they responded favorably.  We should tweet/DM them and then mark them
            as having reciprocated follow.

            In case 2, we're just awesome.  Just add them as if they have
            reciprocated follow (basically, they're good, we just need them
            in the database)
        """

        print "[Check for untracked followers]"
        followers_ids_api = self.api.followers_ids()[0]
        followers_ids_django = [t.hunted.twitter_id for t in Target.objects\
                .filter(hunter=self.user)\
                .filter(status=Target.FOLLOWER)
            ]

        untracked_followers_ids = filter(
            lambda x: unicode(x) not in followers_ids_django,
            followers_ids_api)

        #TODO: REMOVE ME
        untracked_followers_ids = untracked_followers_ids[:]

        untracked_followers, remainder = lookup_users_by_id(self.api, untracked_followers_ids)
        for untracked_follower in untracked_followers:
            twitter_account, created = utils.get_or_create_twitter_account(untracked_follower)
            target, created = Target.objects.get_or_create(
                hunter = self.user,
                hunted = twitter_account,
                )
            if target.status == Target.PURGATORY:
                # Yay someone we targeted reciprocated follow
                self.contact(target.hunted)
                pass
            else:
                print target.status
                # Either a totally external follow,
                # an ingrate changed mind, or someone who we
                # chatted became interested and followed
                self.contact(target.hunted)
                pass
            # Either way the action is the same, follow him
            target.status = Target.FOLLOWER
            target.save()
            print "  - add follower: %s" % twitter_account.screen_name

    def prune_losers(self):
        """Unfollow people who are uninterested in following us.

           When a user is followed by twittermarketing, they're added to a list
           of users we are following.  If after $RECIPROCATION_WINDOW hours
           have elapsed, that user hasn't followed us back, unfollow them to
           make room for us to follow other people.
        """

        print "[Prune losers]"
        # check to see if people i followed follow me back
        cutoff_time = datetime.now() - timedelta(hours=reciprocation_window)
        ingrates = Target.objects.filter(
            hunter=self.user,
            status=Target.PURGATORY,
            modified__lt=cutoff_time) # They didn't follow back in time

        for ingrate in ingrates:
            ingrate.status = Target.INGRATE
            ingrate.save()
            print "  - Unfollowed %s" % ingrate.hunted.screen_name
            try:
                self.api.destroy_friendship(ingrate.hunted)
            except Exception, e:
                print e
                return
            finally:
                self.contact(ingrate)


    def contact(self, persontocontact, msg=None):
        print "CONTACT THE NEW GUY"
        return

#         if False:
#             """
#             This doesn't actually work.
#             """
#             if random.randint(1, 30) == 10:
#                 status_message = random.sample(status_messages, 1)[0]
#                 api.update_status("@%s %s" % (new_follower.screen_name, \
#                                               status_message))
#                 print "    - Updated status to: %s" % new_follower.screen_name
#             else:
#                 direct_message = random.sample(direct_messages, 1)[0]
#                 api.send_direct_message(user_id=new_follower.twitter_id,
#                                         text=direct_message)
#                 print "    - Sent DM to: %s" % new_follower.screen_name

    def find_new_followers(self):
        api = self.api
        """Find new followers and dump them in the db"""

        # Find statuses that match our interests
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

        # Get all the screen names of senders and receivers
        screen_names = [t.to_user for t in statuses if t.to_user] + \
                       [t.from_user for t in statuses]

        # Convert the strings to Tweepy user objects
        users, remainder = lookup_users_by_screen_name(self.api, screen_names)

        for user in users:
            twitter_account, created = utils.get_or_create_twitter_account(user)
            if created:
                print "    - Save TwitterAccount: %s to django db" % twitter_account.screen_name
            target, created = Target.objects.get_or_create(
                hunter = self.user,
                hunted = twitter_account,
                )
            if created:
                try:
                    trigger_tweet = filter(
                        lambda x: x.from_user.lower() == user.screen_name.lower(),
                        statuses)[0].text
                    print "    - Trigger:", trigger_tweet
                except Exception, e:
                    print "WEIRD ERROR FINDING TWEET"
                    try:
                        print from_user.lower()
                        print user.screen_name.lower()
                    except Exception, e:
                        print e
                    trigger_tweet = "Error: Couldn't retrieve tweet."
                target.reason = trigger_tweet
                target.status = Target.ON_DECK
                target.save()
            else:
                pass
                # print "    - Previously followed this dudesicle: %s" % user.screen_name


    def follow_user(self, target):
        """This is one of 2 possible actions we can take.
            We're either interested in following ppl or tweeting people.
        """
        try:
            self.api.create_friendship(target.hunted.screen_name)
            print "    - Followed: %s" % target.hunted.screen_name
        except Exception, e:
            raise Exception, e
        else:
            # Write record of new follow to db
            target.status = Target.PURGATORY
            target.save()

    def tweet_user(self, target):
        """This is one of 2 possible actions we can take.
            We're either interested in following ppl or tweeting people.
        """
        print "Tweet at user: %s" % target.hunted.screen_name


    def initiate_contact(self):
        """Loop through the people on deck and start contacting them until exception"""
        candidates = Target.objects.filter(hunter=self.user, status=Target.ON_DECK)
        print "[Start initiating contact: %s]" % candidates.count()

        for target in candidates:
            try:
                if self.strategy == UserProfile.FOLLOW:
                    self.follow_user(target)
                elif self.strategy == UserProfile.TWEET:
                    # Do the tweet strategy
                    pass
                else:
                    pass
            except Exception, e:
                print e
                return

        # while not exception, keep popping items off db and reaching out
