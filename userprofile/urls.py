from django.urls import path
from . import views

app_name = 'userprofile'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.my_profile, name='my_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('<int:user_id>/', views.public_profile, name='public_profile'),
]