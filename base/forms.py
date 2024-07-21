# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    catchy_line = forms.CharField(label="One Catchy Line About You", max_length=500, widget=forms.TextInput(attrs={'placeholder': 'It can be anything, a quote, a joke, anything!'}))
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = Profile(user=user, catchy_line=self.cleaned_data['catchy_line'], avatar=self.cleaned_data.get('avatar'))
            profile.save()
        return user

class EditProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    catchy_line = forms.CharField(label="One Catchy Line About You", max_length=500, required=False)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ['email', 'catchy_line', 'avatar']

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.email = self.cleaned_data['email']
        if commit:
            profile.user.save()
            profile.save()
        return profile

class PasswordChangingForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(PasswordChangingForm, self).__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter current password'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter new password'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm new password'})
