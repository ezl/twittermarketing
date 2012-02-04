from django.views.generic.simple import direct_to_template

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm



def index(request):
    template = "index.html"

    ctx = dict(
        var  = "ADFADA",
    )
    return direct_to_template(request, template, ctx)
