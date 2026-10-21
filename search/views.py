from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from item.models import Item


def get_filtered_items(request):
    """
    Fungsi helper untuk menyaring barang berdasarkan parameter GET:
    - q / input: pencarian nama atau deskripsi
    - category: daftar kategori yang dipilih
    - location: lokasi (bisa teks bebas atau pilihan kota)
    - condition: kondisi barang (baru, baik, cukup)
    - min_price & max_price: rentang harga
    - sort: pengurutan (latest, price_asc, price_desc, name_asc)
    """
    items = Item.objects.filter(status='tersedia').prefetch_related('images')

    # 1. Pencarian Kata Kunci (Keyword Search)
    query = request.GET.get('q', '').strip() or request.GET.get('input', '').strip()
    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # 2. Filter Kategori (Checkbox / URL Param)
    categories = request.GET.getlist('category')
    # Support juga jika category dikirim sebagai string dipisah koma
    if not categories and request.GET.get('category'):
        categories = [c.strip() for c in request.GET.get('category').split(',') if c.strip()]
    if categories:
        items = items.filter(category__in=categories)

    # 3. Filter Lokasi (Checkbox / Free Text)
    locations = request.GET.getlist('location')
    if not locations and request.GET.get('location'):
        loc_str = request.GET.get('location').strip()
        if ',' in loc_str:
            locations = [l.strip() for l in loc_str.split(',') if l.strip()]
        else:
            locations = [loc_str]
    if locations:
        loc_filter = Q()
        for loc in locations:
            loc_filter |= Q(location__icontains=loc)
        items = items.filter(loc_filter)

    # 4. Filter Kondisi Barang
    conditions = request.GET.getlist('condition')
    if not conditions and request.GET.get('condition'):
        conditions = [c.strip() for c in request.GET.get('condition').split(',') if c.strip()]
    if conditions:
        items = items.filter(condition__in=conditions)

    # 5. Filter Rentang Harga (Min & Max)
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            items = items.filter(price__gte=float(min_price))
        except ValueError:
            pass

    max_price = request.GET.get('max_price')
    if max_price:
        try:
            items = items.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # 6. Pengurutan (Sorting)
    sort = request.GET.get('sort', 'latest')
    if sort == 'price_asc':
        items = items.order_by('price')
    elif sort == 'price_desc':
        items = items.order_by('-price')
    elif sort == 'name_asc':
        items = items.order_by('name')
    else:  # default 'latest'
        items = items.order_by('-created_at')

    return items


def search_page(request):
    """
    Halaman utama pencarian & filter barang.
    Menampilkan UI lengkap dengan sidebar filter dan daftar barang awal.
    """
    items = get_filtered_items(request)

    # Ambil daftar lokasi unik yang ada di database
    db_locations = list(Item.objects.values_list('location', flat=True).distinct())
    clean_locations = sorted(list({loc.strip() for loc in db_locations if loc and loc.strip()}))
    
    # Jika database masih kosong/sedikit, sertakan default kota populer
    default_locations = ['Jakarta', 'Depok', 'Bandung', 'Bogor', 'Tangerang', 'Bekasi', 'Surabaya', 'Yogyakarta']
    all_locations = sorted(list(set(clean_locations + default_locations)))

    initial_query = request.GET.get('q', '').strip() or request.GET.get('input', '').strip()
    selected_category = request.GET.get('category', '')
    selected_categories = request.GET.getlist('category')
    if not selected_categories and selected_category:
        selected_categories = [c.strip() for c in selected_category.split(',') if c.strip()]

    context = {
        'items': items,
        'categories': Item.CATEGORY_CHOICES,
        'conditions': Item.CONDITION_CHOICES,
        'locations': all_locations,
        'initial_query': initial_query,
        'selected_categories': selected_categories,
        'selected_category': selected_category,
        'total_items': items.count(),
    }
    return render(request, 'search/search.html', context)


def search_api(request):
    """
    Endpoint AJAX JSON untuk menyaring barang secara real-time
    tanpa reload halaman. Dipanggil oleh JavaScript di frontend.
    """
    items = get_filtered_items(request)

    data = []
    for item in items:
        cover = item.cover_image
        image_url = cover.image.url if cover and cover.image else None

        data.append({
            'id': str(item.id),
            'name': item.name,
            'description': item.description[:100] + ('...' if len(item.description) > 100 else ''),
            'category_code': item.category,
            'category_display': item.get_category_display(),
            'price': float(item.price),
            'formatted_price': f"Rp{int(item.price):,}".replace(',', '.'),
            'location': item.location,
            'condition': item.get_condition_display(),
            'status': item.status,
            'status_display': item.get_status_display(),
            'image_url': image_url,
            'detail_url': reverse('item:item_detail', kwargs={'pk': item.pk}),
        })

    return JsonResponse({
        'status': 'success',
        'count': len(data),
        'items': data,
    })
