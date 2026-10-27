from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_page, name='search_page'),
    path('api/', views.search_api, name='search_api'),
    path('history/clear/', views.clear_search_history, name='clear_search_history'),
    path('history/<int:pk>/delete/', views.delete_search_history, name='delete_search_history'),
]
