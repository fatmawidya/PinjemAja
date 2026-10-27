import json
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
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

@require_POST
def register_htmx(request):
    form = RegisterForm(request.POST)
    if form.is_valid():
        user = form.save()
        login(request, user)
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('userprofile:my_profile')
        return response

    response = render(request, 'userprofile/partials/register_form.html', {'form': form})
    response['HX-Trigger'] = json.dumps({
        'showToast': {'title': 'Gagal mendaftar', 'message': 'Periksa kembali data yang kamu masukkan.', 'type': 'error'}
    })
    return response

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

@require_POST
def login_htmx(request):
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('landing_page')
        return response

    response = render(request, 'userprofile/partials/login_form.html', {'form': form})
    response['HX-Trigger'] = json.dumps({
        'showToast': {'title': 'Gagal login', 'message': 'Username atau password salah.', 'type': 'error'}
    })
    return response

def logout_view(request):
    logout(request)
    return redirect('landing_page')

@login_required
def my_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'userprofile/my_profile.html', {'profile': profile, 'active_menu': 'profil'})

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
    return render(request, 'userprofile/edit_profile.html', {'form': form, 'active_menu': 'profil'})

@require_POST
@login_required
def edit_profile_htmx(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST, request.FILES, instance=profile)

    if form.is_valid():
        form.save()
        response = render(request, 'userprofile/partials/edit_profile_form.html', {'form': form, 'profile': profile})
        response['HX-Trigger'] = json.dumps({
            'showToast': {'title': 'Berhasil', 'message': 'Profil berhasil diperbarui!', 'type': 'success'}
        })
        return response

    response = render(request, 'userprofile/partials/edit_profile_form.html', {'form': form, 'profile': profile})
    response['HX-Trigger'] = json.dumps({
        'showToast': {'title': 'Gagal menyimpan', 'message': 'Periksa kembali data yang kamu masukkan.', 'type': 'error'}
    })
    return response

@login_required
def public_profile(request, user_id):
    profile = get_object_or_404(Profile, user__id=user_id)
    return render(request, 'userprofile/public_profile.html', {'profile': profile})

@login_required
@require_POST
def delete_avatar(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if profile.avatar:
        profile.avatar.delete(save=False)
        profile.avatar = None
        profile.save()
        message, toast_type = 'Foto profil berhasil dihapus.', 'success'
    else:
        message, toast_type = 'Belum ada foto profil untuk dihapus.', 'normal'

    form = ProfileForm(instance=profile)
    response = render(request, 'userprofile/partials/edit_profile_form.html', {
        'form': form, 'profile': profile
    })
    response['HX-Trigger'] = json.dumps({
        'showToast': {'title': 'Foto Profil', 'message': message, 'type': toast_type}
    })
    return response