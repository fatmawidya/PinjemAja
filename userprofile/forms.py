from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'nama@email.com'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username kamu'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'bio', 'avatar']  
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '081234567890'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ceritakan sedikit tentang dirimu...'}),
        }