import site
import sys
import os

site.addsitedir('/home/ezl/.virtualenvs/twittermarketing/lib/python2.6/site-packages/')
sys.path.append('/home/ezl/code/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

