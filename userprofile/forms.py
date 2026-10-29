import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, PAYMENT_PROVIDERS, EWALLETS

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
        fields = ['phone_number', 'bio', 'avatar', 'payment_provider', 'payment_number', 'payment_holder']
        labels = {
            'phone_number': 'Nomor Telepon',
            'bio': 'Tentang Saya',
            'avatar': 'Foto Profil',
        }
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'placeholder': '081234567890',
                'class': 'form-control',
            }),
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Ceritakan sedikit tentang dirimu...',
                'class': 'form-control',
            }),
            # FileInput biasa tidak menampilkan checkbox Clear/Change.
            'avatar': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'd-none',
            }),
            'payment_provider': forms.Select(attrs={'class': 'form-select'}),
            'payment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_holder': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nama sesuai rekening/akun'
            }),
        }

    def clean(self):
        data = super().clean()
        provider = data.get('payment_provider', '')
        number = (data.get('payment_number') or '').strip()
        holder = (data.get('payment_holder') or '').strip()
        data['payment_number'], data['payment_holder'] = number, holder

        if provider or number or holder:
            if not (provider and number and holder):
                raise forms.ValidationError('Lengkapi metode, nomor, dan nama pemilik, atau kosongkan semuanya.')
            if provider in EWALLETS:
                if not re.fullmatch(r'08\d{8,11}', number):
                    self.add_error('payment_number', 'Nomor e-wallet harus nomor HP (contoh: 081234567890).')
            elif not re.fullmatch(r'\d{10,16}', number):
                self.add_error('payment_number', 'Nomor rekening harus 10-16 digit angka.')
        return data

class UserEmailForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email sudah dipakai.')
        return email