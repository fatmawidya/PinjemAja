from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from item.models import Item
from .models import SearchHistory
from .forms import SearchForm


def save_search_history(request, query):
    """
    Menyimpan kata kunci pencarian ke SearchHistory untuk fitur riwayat pencarian (CRUD).
    """
    if not query or len(query.strip()) < 2:
        return
    q = query.strip()
    user = request.user if request.user.is_authenticated else None

    # Cek pencarian terakhir agar tidak ada duplikasi berturut-turut
    last_search = SearchHistory.objects.filter(user=user).first()
    if not last_search or last_search.keyword.lower() != q.lower():
        SearchHistory.objects.create(user=user, keyword=q)


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
    items = (Item.objects.filter(status='tersedia')
             .select_related('owner__profile').prefetch_related('images'))

    # 1. Pencarian Kata Kunci (Keyword Search)
    query = request.GET.get('q', '').strip() or request.GET.get('input', '').strip()
    if query:
        save_search_history(request, query)
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

    # Cek jika ada request khusus 'nearby=1' memakai kota dari user profile
    if (request.GET.get('nearby') == '1' or request.GET.get('nearest') == '1') and request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.city:
            user_city_nearby = request.user.profile.city.strip()
            if user_city_nearby and user_city_nearby not in locations:
                locations.append(user_city_nearby)

    if locations:
        loc_filter = Q()
        for loc in locations:
            # Lokasi barang = lokasi pemilik (profil): cocokkan kota atau provinsi
            loc_filter |= (Q(owner__profile__city__icontains=loc)
                           | Q(owner__profile__province__icontains=loc))
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

    # Ambil daftar lokasi unik yang ada di database (dari profil pemilik)
    db_locations = list(Item.objects.values_list('owner__profile__city', flat=True).distinct())
    clean_locations = sorted(list({loc.strip().title() for loc in db_locations if loc and loc.strip()}))

    # Jika database masih kosong/sedikit, sertakan default kota populer
    default_locations = ['Jakarta', 'Depok', 'Bandung', 'Bogor', 'Tangerang', 'Bekasi', 'Surabaya', 'Yogyakarta']
    all_locations = sorted(list(set(clean_locations + default_locations)))

    initial_query = request.GET.get('q', '').strip() or request.GET.get('input', '').strip()
    selected_category = request.GET.get('category', '')
    selected_categories = request.GET.getlist('category')
    if not selected_categories and selected_category:
        selected_categories = [c.strip() for c in selected_category.split(',') if c.strip()]

    # Ambil 5 riwayat pencarian terakhir
    user = request.user if request.user.is_authenticated else None
    search_histories = SearchHistory.objects.filter(user=user)[:5]
    form = SearchForm(request.GET)

    user_city = None
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.city:
        user_city = request.user.profile.city.strip()

    context = {
        'items': items,
        'form': form,
        'user_city': user_city,
        'categories': Item.CATEGORY_CHOICES,
        'conditions': Item.CONDITION_CHOICES,
        'locations': all_locations,
        'initial_query': initial_query,
        'selected_categories': selected_categories,
        'selected_category': selected_category,
        'total_items': items.count(),
        'search_histories': search_histories,
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

        # Gunakan lokasi dari profil pemilik agar konsisten dengan filter
        profile = getattr(item.owner, 'profile', None)
        location_display = profile.city if profile and profile.city else (item.location or '')

        # Gunakan properti dinamis display_status dari Item
        display_status = item.display_status
        if display_status == 'tersedia':
            status_display = 'Tersedia'
            is_available = True
        elif display_status == 'dipinjam':
            status_display = 'Terpinjam'
            is_available = False
        elif display_status == 'pending':
            status_display = 'Menunggu Konfirmasi'
            is_available = False
        else:
            status_display = 'Tidak Tersedia'
            is_available = False

        data.append({
            'id': str(item.id),
            'name': item.name,
            'description': item.description[:100] + ('...' if len(item.description) > 100 else ''),
            'category_code': item.category,
            'category_display': item.get_category_display(),
            'price': float(item.price),
            'formatted_price': f"Rp{int(item.price):,}".replace(',', '.'),
            'location': location_display,
            'condition': item.get_condition_display(),
            'status': display_status,           # status dinamis
            'status_display': status_display,   # label untuk UI
            'is_available': is_available,       # flag untuk frontend
            'image_url': image_url,
            'detail_url': reverse('item:item_detail', kwargs={'pk': item.pk}),
        })

    # Kirim daftar riwayat pencarian terbaru untuk update AJAX frontend
    user = request.user if request.user.is_authenticated else None
    histories = SearchHistory.objects.filter(user=user)[:5]
    history_list = [{'id': h.pk, 'keyword': h.keyword} for h in histories]

    return JsonResponse({
        'status': 'success',
        'count': len(data),
        'items': data,
        'history': history_list,
    })


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def delete_search_history(request, pk):
    """
    Menghapus 1 kata kunci dari riwayat pencarian (CRUD - Delete).
    """
    try:
        user = request.user if request.user.is_authenticated else None
        item = SearchHistory.objects.get(pk=pk, user=user)
        item.delete()
        return JsonResponse({'status': 'success', 'message': 'Riwayat berhasil dihapus.'})
    except SearchHistory.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Riwayat tidak ditemukan.'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def clear_search_history(request):
    """
    Membersihkan semua riwayat pencarian user (CRUD - Delete all).
    """
    user = request.user if request.user.is_authenticated else None
    SearchHistory.objects.filter(user=user).delete()
    return JsonResponse({'status': 'success', 'message': 'Semua riwayat berhasil dibersihkan.'})