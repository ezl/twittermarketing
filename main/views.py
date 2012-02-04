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
    template_name = "basic_form.html"
    form_class = UserProfileForm
    model = UserProfile
    success_url = "/profile/" #reverse("profile") #FML
    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)


