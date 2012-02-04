from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from main.views import SignUpView, UserProfileView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'main.views.index', name='index'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^accounts/signup/$', SignUpView.as_view(), name='signup'),
    url(r'^profile/$', login_required(UserProfileView.as_view()), name='profile'),
)
