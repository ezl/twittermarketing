from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'main.views.index', name='index'),

    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^signup/$', 'main.views.signup', name='signup'),
)
