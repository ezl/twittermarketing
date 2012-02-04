from django.views.generic.simple import direct_to_template
from django.views.generic.edit import CreateView

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

def index(request):
    template_name = "index.html"

    ctx = dict(
    )
    return direct_to_template(request, template_name, ctx)


class SignUp(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = "/"

