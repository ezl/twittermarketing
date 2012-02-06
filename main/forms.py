from django import forms
from models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user', 'hits_per_query', 'reciprocation_window')

