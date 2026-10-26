from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, ProfileForm
from .models import Profile

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('userprofile:my_profile')
    else:
        form = RegisterForm()
    return render(request, 'userprofile/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('landing_page')
    else:
        form = AuthenticationForm()
    return render(request, 'userprofile/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('landing_page')

@login_required
def my_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'userprofile/my_profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('userprofile:my_profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'userprofile/edit_profile.html', {'form': form})

@login_required
def public_profile(request, user_id):
    profile = get_object_or_404(Profile, user__id=user_id)
    return render(request, 'userprofile/public_profile.html', {'profile': profile})