from main.models import TwitterAccount

def get_or_create_twitter_account(tweepy_user):
    """get or create an internal TwitterAccount object

       from a tweepy user
    """
    screen_name = tweepy_user.screen_name.lower()

    # get the account, or create it if we don't know this person
    twitter_account, created = TwitterAccount.objects.get_or_create(
        screen_name = screen_name
        )
    # if its freshly created, add more info and save it
    if created:
        twitter_account.name          = tweepy_user.name
        twitter_account.twitter_id    = tweepy_user.id
        twitter_account.location      = tweepy_user.location
        twitter_account.description   = tweepy_user.description
        twitter_account.url           = tweepy_user.url
        twitter_account.save()
    return twitter_account, created
