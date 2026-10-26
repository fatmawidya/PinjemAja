from django.conf import settings
from django.db import models


class SearchHistory(models.Model):
    """
    Model untuk mencatat riwayat pencarian kata kunci oleh user.
    Memenuhi kriteria CRUD dan arsitektur database PBP.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_histories'
    )
    keyword = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Search Histories'

    def __str__(self):
        user_str = self.user.username if self.user else 'Guest'
        return f"{user_str}: {self.keyword}"
