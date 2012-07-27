from datetime import datetime, timedelta
import logging
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
        self.log = logging.getLogger("market")
        profiles = UserProfile.objects.filter(marketing_on=True).order_by("-created")
        profiles = UserProfile.objects.filter(user__username="rocketlease", marketing_on=True)
        print "=" * 70
        print "[ Start marketing ]".center(70)
        print "=" * 70
        for profile in profiles:
            # get the user
            user = profile.user

            # get the params of the marketing strategy
            self.geocode = profile.geocode.strip() or None
            self.hits_per_query = profile.hits_per_query
            self.reciprocation_window = profile.reciprocation_window
            self.queries = [q.strip() for q in profile.queries.split("\r\n")]
            self.dms = [q.strip() for q in profile.direct_messages.strip().split("\r\n")]
            self.tweets  = [q.strip() for q in profile.tweets.strip().split("\r\n")]
            if profile.competitors:
                lines = profile.competitors.strip().split("\r\n")
                self.competitors = [q.strip() for q in lines]
            else:
                self.competitors = []
            # Remove empty string
            self.queries = filter(lambda x: bool(x), self.queries)
            self.dms = filter(lambda x: bool(x), self.dms)
            self.tweets = filter(lambda x: bool(x), self.tweets)
            self.competitors = filter(lambda x: bool(x), self.competitors)
            if (len(self.queries) == 0 and not self.strategy == UserProfile.STEAL) or len(self.dms) == 0 or len(self.tweets) == 0:
                continue

            self.strategy = profile.strategy

            try:
                api = utils.get_user_api(user)
                print "[ Start marketing for %s ]" % user
                self.api = api
                self.user = user
                self.me = api.me()
                print "friends: %s, followers %s" % (self.me.friends_count,
                                                     self.me.followers_count)
                # Do work
                # ----
                # DB consistency operations -- make sure our sheets match
                # twitter sheets.  we track adds, not deletes.
                # This takes a long time, we can move it to its own function
                # later to run daily instead of hourly

                self.add_untracked_friends()
                self.add_untracked_followers()

                #main work
                self.prune_losers()

                self.find_new_followers()
                self.initiate_contact()

                print "DONE with %s" % self.me.screen_name
                print
            except Exception, e:
                raise

    def add_untracked_friends(self):
        """Add previously untracked users.

        If a person is manually followed through the twitter website, this
        app doesn't know that a relationship exists.

        This method adds untracked people to our repository so we know not
        to refollow them and we won't multiple message them."""

        self.log.debug("CHECK FOR UNTRACKED FRIENDS")
        friends_ids_api = self.api.friends_ids()
        targets = Target.objects.filter(hunter=self.user)\
                      .exclude(status__in=Target.ON_DECK)
        friends_ids_django = [t.hunted.twitter_id for t in targets]
        untracked_friends_ids = \
            filter(lambda x: unicode(x) not in friends_ids_django,
                   friends_ids_api)

        untracked_friends, remainder = lookup_users_by_id(self.api,
                                                          untracked_friends_ids)
        for untracked_friend in untracked_friends:
            twitter_account, created = utils.get_or_create_twitter_account(
                                           untracked_friend)
            target, created = Target.objects.get_or_create(
                                  hunter=self.user, hunted=twitter_account)
            target.reason = "External add."
            target.status = Target.FOLLOWER
            target.save()
            self.log.debug("  => add friend: %s" % twitter_account.screen_name)

    def add_untracked_followers(self):
        """Add previously untracked users.

        These are people that are following us, but the django database doesn't
        know about.  What that means is that they started following us since the
        last run of this function.

        There are 2 reasons that happens:

        1) We followed them, then they started following us
        2) They randomly decided to start following us or we tweeted at them
        and they started following us.

        In case 1, that means we had initially put them into purgatory and they
        responded favorably.  We should tweet/DM them and then mark them as
        having reciprocated follow.

        In case 2, we're just awesome.  Just add them as if they have
        reciprocated follow (basically, they're good, we just need them in the
        database)
        """

        self.log.debug("CHECK FOR UNTRACKED FOLLOWERS")
        followers_ids_api = self.api.followers_ids()
        target = Target.objects.filter(hunter=self.user)\
                     .filter(status=Target.FOLLOWER)
        followers_ids_django = [t.hunted.twitter_id for t in target]

        untracked_followers_ids = filter(
            lambda x: unicode(x) not in followers_ids_django,
            followers_ids_api)

        untracked_followers, remainder = lookup_users_by_id(self.api,
                                             untracked_followers_ids)
        for untracked_follower in untracked_followers:
            twitter_account, created = \
                utils.get_or_create_twitter_account(untracked_follower)
            target, created = Target.objects.get_or_create(
                hunter=self.user, hunted=twitter_account)
            if target.status == Target.PURGATORY:
                # Yay someone we targeted reciprocated follow
                self.follow_reciprocated(target)
            else:
                print target.status
                # Either a totally external follow, an ingrate changed mind,
                # or someone who we chatted became interested and followed
            # Either way the action is the same, follow him
            target.status = Target.FOLLOWER
            target.save()
            self.log.debug("  => Add follower: %s" % twitter_account.screen_name)

    def prune_losers(self):
        """Unfollow people who are uninterested in following us.

        When a user is followed by twittermarketing, they're added to a list
        of users we are following.  If after $RECIPROCATION_WINDOW hours
        have elapsed, that user hasn't followed us back, unfollow them to
        make room for us to follow other people.
        """
        self.log.debug("PRUNE LOSERS")
        # check to see if people i followed follow me back
        cutoff_time = (datetime.now()
                       - timedelta(hours=self.reciprocation_window))
        ingrates = Target.objects.filter(
            hunter=self.user, status=Target.PURGATORY,
            modified__lt=cutoff_time) # They didn't follow back in time

        for ingrate in ingrates:
            ingrate.status = Target.INGRATE
            ingrate.save()
            self.log.debug("  => Unfollowed %s" % ingrate.hunted.screen_name)
            try:
                self.api.destroy_friendship(ingrate.hunted)
            except Exception, e:
                print e
                return
            finally:
                self.contact(ingrate)

    def find_new_followers(self):
        """Find new followers and dump them in the db"""
        api = self.api
        geocode = self.geocode
        queries = self.queries
        hits_per_query = self.hits_per_query

        self.log.debug("Initialize")

        if self.strategy == UserProfile.FOLLOW or self.strategy == UserProfile.TWEET:
            # Find statuses that match our interests
            self.log.debug("Strategy set to FOLLOW or TWEET")
            n = hits_per_query
            search_dict = dict()
            search_dict['lang'] = "en"
            if not geocode is None:
                search_dict['geocode'] = geocode
            statuses = list()
            self.log.debug("Queries:")
            for q in queries:
                search_dict['q'] = q
                results = [c for c in Cursor(api.search, **search_dict).items(n)]
                self.log.debug("  => %s: %s hits" % (q, len(results)))
                statuses.extend(results)
            #self.log.debug("Statuses: %s" % "\n".join([str(s.__dict__) for s in statuses]))
            # Get all the screen names of senders and receivers
            screen_names = ([t.from_user for t in statuses] +
                            [t.to_user for t in statuses if t.to_user])

            # Convert the strings to Tweepy user objects
            users, remainder = lookup_users_by_screen_name(self.api, screen_names)

        elif self.strategy == UserProfile.STEAL:
            users = []
            print self.competitors
            for competitor in self.competitors:
                try:
                    competitor_friends_ids = self.api.friends_ids(competitor)[0]
                    competitor_followers_ids = self.api.followers_ids(competitor)[0]

                    if True:
                        new_competitor_friends_ids = [id for id in competitor_friends_ids if not len(TwitterAccount.objects.filter(twitter_id=id)) > 0 ]
                        old_competitor_friends_ids = [id for id in competitor_friends_ids if len(TwitterAccount.objects.filter(twitter_id=id)) > 0 ]
                        new_competitor_followers_ids = [id for id in competitor_followers_ids if not len(TwitterAccount.objects.filter(twitter_id=id)) > 0 ]
                        old_competitor_followers_ids = [id for id in competitor_followers_ids if len(TwitterAccount.objects.filter(twitter_id=id)) > 0 ]
                        print new_competitor_friends_ids
                        print old_competitor_friends_ids
                        print new_competitor_followers_ids
                        print old_competitor_followers_ids

                    new_competitor_friends, remaining_friends = utils.lookup_users_by_id(self.api, new_competitor_friends_ids)
                    new_competitor_followers, remaining_followers = utils.lookup_users_by_id(self.api, new_competitor_followers_ids)

                except Exception, e:
                    print e
                    # didn't get all the users, don't remove the competitor
                    # from the competitor list
                    pass
                else:
                    # got all the competitors friends and followers and converted them
                    # to tweepy users.
                    users += new_competitor_friends
                    users += new_competitor_followers
                    # add them to the users list to be processed in the next block (for user in users)
                    # then pop the name off the competitors list in the UserProfile
                    pass
                # return # for now

            # use the profile competitors list
            # for each name in competitors list
            # add all friends

        for user in users:
            twitter_account, created = utils.get_or_create_twitter_account(user)
            target, created = Target.objects.get_or_create(
                hunter=self.user, hunted=twitter_account)
            if created:
                try:
                    screen_name = user.screen_name.lower()
                    match = lambda x: screen_name in \
                        (x.from_user.lower(), x.to_user and x.to_user.lower())
                    if not self.strategy == UserProfile.STEAL:
                        trigger_tweet = filter(match, statuses)[0].text
                    else:
                        trigger_tweet = "Steal from user: %s" % user.screen_name # actually this is wrong... i want to write the correct competitor down, but we don't have that information -- we'd have to embed it in the for competitor in self.competitors loop
                except Exception, e:
                    self.log.exception("Could not get trigger tweet for %s" %
                                       user.screen_name.lower())
                    trigger_tweet = "Error: Couldn't retrieve tweet."
                self.log.debug("Saved twitter account %s (trigger: %r)" %
                               (twitter_account.screen_name,
                                trigger_tweet[:50]))
                target.reason = trigger_tweet
                target.status = Target.ON_DECK
                target.save()
            else:
                pass
                # print "    - Previously followed this dudesicle: %s" % user.screen_name

    def follow_user(self, target):
        """This is one of 2 possible actions we can take. We're either
        interested in following people or tweeting people."""
        try:
            self.api.create_friendship(target.hunted.screen_name)
            self.log.debug("Followed: %s" % target.hunted.screen_name)
        except Exception, e:
            self.log.exception("Could not follow %s" %
                               target.hunted.screen_name)
        else:
            # Write record of new follow to db
            target.status = Target.PURGATORY
            target.save()

    def dm_user(self, target, msg=None):
        self.log.debug("DM'ing %s" % target.hunted.screen_name)
        direct_message = random.sample(self.dms, 1)[0]
        self.api.send_direct_message(screen_name=target.hunted.screen_name,
                                     text=direct_message)

    def tweet_user(self, target, msg=None):
        """This is one of 2 possible actions we can take.
            We're either interested in following ppl or tweeting people.
        """
        self.log.debug("Tweeting %s" % target.hunted.screen_name)
        tweet = "@%s: %s" % (target.hunted.screen_name,
                             random.sample(self.tweets, 1)[0])
        tweet = tweet [:140]
        self.api.update_status(tweet)
        target.status = Target.FOLLOWER
        target.save()

    def follow_reciprocated(self, target):
        """When someone reciprocates a follow,  either DM or @reply."""
        if random.randint(1, 20) == 1: # 1 in 20 are public @replies
            self.tweet_user(target)
        else:
            try:
                self.dm_user(target)
            except:
                pass

    def initiate_contact(self):
        strategy = self.strategy
        """Loop through the people on deck and start contacting them until
        exception."""
        candidates = Target.objects.filter(hunter=self.user,
                                           status=Target.ON_DECK)
        self.log.debug("Start initiating contact with %d people" %
                       candidates.count())

        for target in candidates:
            try:
                if (strategy == UserProfile.FOLLOW or
                    strategy == UserProfile.STEAL):
                    self.follow_user(target)
                elif strategy == UserProfile.TWEET:
                    self.follow_user(target)
                else:
                    pass
            except Exception, e:
                print e # probably the rate limit
                return

        # while not exception, keep popping items off db and reaching out
