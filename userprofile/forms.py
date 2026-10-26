from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'bio', 'avatar']
        labels = {
            'phone_number': 'Nomor HP',
            'address': 'Alamat',
            'bio': 'Bio',
            'avatar': 'Foto Profil',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }