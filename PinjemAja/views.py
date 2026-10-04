from django.shortcuts import render
from item.models import Item


def landing_page(request):
    recommended_items = (
        Item.objects.exclude(status='tidak_tersedia')
        .prefetch_related('images')[:5]
    )
    return render(request, 'index.html', {'recommended_items': recommended_items})