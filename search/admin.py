from django.contrib import admin
from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('keyword', 'user__username')
