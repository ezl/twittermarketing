from django.views.generic.simple import direct_to_template
from django.views.generic.edit import CreateView, UpdateView
from django.core.urlresolvers import reverse

# from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from forms import UserProfileForm
from models import UserProfile


def index(request):
    template_name = "index.html"

    ctx = dict(
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

    twitteruser = dict(
        screen_name     = me.screen_name,
        name            = me.name,
        twitter_id      = me.id,
        location        = me.location,
        description     = me.description,
        url             = me.url,
        followers_count = me.followers_count,
        friends_count   = me.friends_count,
        listed_count    = me.listed_count,
        )
    return HttpResponseRedirect("/")

def twitter_signin(request):
    auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    auth_url = auth.get_authorization_url()

    request.session['unauthed_token'] = auth.request_token
    response = HttpResponseRedirect(auth_url)
    return response


class SignUpView(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = "/" # reverse("index") #WTF WHY CANT I REVERSE?!~
    def form_valid(self, form):
        # success message
        # log in
        form.save()
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        login(self.request, user)
        print "PADFAD"
        return super(SignUpView, self).form_valid(form)

class UserProfileView(UpdateView):
    template_name = "userprofile.html"
    form_class = UserProfileForm
    model = UserProfile
    success_url = "/profile/" #reverse("profile") #FML
    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)


