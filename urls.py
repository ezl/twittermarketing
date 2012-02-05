from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from main.views import UserProfileView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'main.views.index', name='index'),
    url(r'^twitter/signin/$', 'main.views.twitter_signin', name='twitter_signin'),
    url(r'^twitter/done/$', 'main.views.twitter_done', name='twitter_done'),
    url(r'^twitter/test_tweet/$', 'main.views.test_tweet', name='test_tweet'),

    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^profile/$', login_required(UserProfileView.as_view()), name='profile'),
)
