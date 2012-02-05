from django.views.generic.simple import direct_to_template
from django.views.generic.edit import CreateView, UpdateView
from django.core.urlresolvers import reverse

# from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from forms import UserProfileForm
from models import UserProfile, TwitterAccount, TwitterAccountSnapshot


def index(request):
    template_name = "index.html"

    ctx = dict(
        snapshots = TwitterAccountSnapshot.objects.filter(twitter_acount__user=request.user)
    )
    return direct_to_template(request, template_name, ctx)

import tweepy

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse

# Thanks to http://djangosnippets.org/snippets/1353/

def twitter_done(request):
    token = request.session.get('unauthed_token', None)
    if not token:
        return HttpResponse("No un-authed token cookie")
    if token.key != request.GET.get('oauth_token'):
        return HttpResponse("Something went wrong! Tokens do not match")

    auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    auth.request_token = token

    oauth_token = request.REQUEST.get('oauth_token') # unnecessary
    oauth_verifier = request.REQUEST.get('oauth_verifier')
    auth.get_access_token(oauth_verifier)

    ACCESS_KEY = auth.access_token.key
    ACCESS_SECRET = auth.access_token.secret
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

    api = tweepy.API(auth)
    me = api.me()

    screen_name = me.screen_name.lower()

    # Create an account for this twitter user if we haven't before
    user, created = User.objects.get_or_create(username=screen_name)
    if created:
        user.set_password(me.id)
        user.save()

    # Log user in
    user = authenticate(
        username = screen_name,
        password = me.id
    )
    login(request, user)

    # get the account, or create it if we don't know this person
    twitter_account, created = TwitterAccount.objects.get_or_create(
        user        = request.user,
        screen_name = screen_name,
        )
    # if its freshly created, add more info and save it
    if created:
        twitter_account.name        = me.name,
        twitter_account.twitter_id  = me.id,
        twitter_account.location    = me.location,
        twitter_account.description = me.description,
        twitter_account.url         = me.url,
        twitter_account.save()

    # Take a snapshot of the account
    twitter_account_snapshot = TwitterAccountSnapshot(
        twitter_account = twitter_account,
        followers_count = me.followers_count,
        friends_count   = me.friends_count,
        listed_count    = me.listed_count,
        )
    twitter_account_snapshot.save()

    return HttpResponseRedirect("/")

def twitter_signin(request):
    auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    auth_url = auth.get_authorization_url()

    request.session['unauthed_token'] = auth.request_token
    response = HttpResponseRedirect(auth_url)
    return response


class UserProfileView(UpdateView):
    template_name = "userprofile.html"
    form_class = UserProfileForm
    model = UserProfile
    success_url = "/profile/" #reverse("profile") #FML
    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)


