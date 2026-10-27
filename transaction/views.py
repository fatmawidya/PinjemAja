from datetime import date
import json
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse

from .models import Transaksi
from item.models import Item
from .forms import FormPinjam, FormUploadBukti

# Create your views here.
@login_required
def form_pinjam(request, barang_id):
    barang = get_object_or_404(Item, pk=barang_id)

    if barang.owner == request.user:
        messages.error(request, "Tidak bisa pinjam barang sendiri.")
        # ini pop up kan brrti redirectnya jg ke page yg per barang itu
        return redirect('item:item_detail', pk=barang_id)

    form = FormPinjam(request.POST or None)

    if request.method == "POST" and form.is_valid():
        t = form.save(commit=False)
        t.barang = barang
        t.peminjam = request.user
        t.pemilik = barang.owner
        t.status = "menunggu_verifikasi"
        t.save()
        messages.success(request, "Permintaan berhasil diajukan!")
        return redirect('item:item_detail', pk=barang_id)

    context = {
        "barang": barang,
        "form": form,
    }
    return render(request, "form_pinjam.html", context)
    
@login_required
def riwayat_meminjam(request):
    status_filter = request.GET.get("status", "semua")
    transaksi_list = _get_transaksi_list(request.user, status_filter, 'peminjam')
    context = {'transaksi_list': transaksi_list, 'status_filter': status_filter, 'is_peminjam': True}
    if _is_ajax(request):
        return render(request, 'partials/transaksi_list.html', context)
    return render(request, 'riwayat_meminjam.html', context)
    
@login_required
def permintaan_masuk(request):
    status_filter = request.GET.get("status", "semua")
    transaksi_list = _get_transaksi_list(request.user, status_filter, 'pemilik')
    context = {'transaksi_list': transaksi_list, 'status_filter': status_filter, 'is_peminjam': False}
    if _is_ajax(request):
        return render(request, 'partials/transaksi_list.html', context)
    return render(request, "permintaan_masuk.html", context)

@login_required
def upload_bukti(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related("barang", "pemilik"),
        pk=transaksi_id,
        peminjam=request.user,
        status="menunggu_pembayaran",
    )
    form = FormUploadBukti(request.POST or None, request.FILES or None, instance=transaksi)

    if request.method == "POST" and form.is_valid():
        transaksi = form.save(commit=False)
        transaksi.status = "menunggu_konfirmasi"
        transaksi.save()
        messages.success(request, "Bukti pembayaran berhasil dikirim.")
        return redirect("transaction:detail_transaksi", transaksi_id=transaksi.pk)

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1

    return render(request, "upload_bukti.html", {
        "transaksi": transaksi,
        "form": form,
        "durasi": durasi,
        "total_harga": transaksi.barang.price * durasi,
    })

@login_required
def detail_transaksi(request, transaksi_id):
    transaksi = get_object_or_404 (Transaksi.objects.select_related("barang", "peminjam", "pemilik"), pk=transaksi_id)

    if request.user.pk not in (transaksi.peminjam_id, transaksi.pemilik_id):
        messages.error(request, "Anda tidak memiliki akses.")
        return redirect("transaction:riwayat_meminjam")

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1
    return render(request, "detail_transaksi.html", {
        "transaksi": transaksi,
        "durasi": durasi,
        "total_harga": transaksi.barang.price * durasi,
        "is_peminjam": request.user == transaksi.peminjam,
    })

@login_required
def edit_transaksi(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi,
        pk=transaksi_id,
        peminjam=request.user,
        status='menunggu_verifikasi',
    )

    if request.method == 'POST':
        form = FormPinjam(request.POST, instance=transaksi)
        if form.is_valid():
            transaksi = form.save(commit=False)

            if transaksi.tanggal_mulai < timezone.localdate():
                form.add_error('tanggal_mulai', 'Tanggal mulai tidak boleh di masa lalu.')
            elif transaksi.tanggal_selesai < transaksi.tanggal_mulai:
                form.add_error('tanggal_selesai', 'Tanggal selesai harus setelah tanggal mulai.')
            else:
                durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1
                transaksi.total_harga = transaksi.barang.price * durasi
                transaksi.save()

                messages.success(request, 'Transaksi berhasil diperbarui.')
                return redirect('transaction:detail_transaksi', transaksi_id=transaksi.id)
    else:
        form = FormPinjam(instance=transaksi)

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1
    return render(request, 'detail_transaksi.html', {
        'transaksi': transaksi,
        'durasi': durasi,
        'total_harga': transaksi.barang.price * durasi,
        'is_peminjam': transaksi.peminjam_id == request.user.pk,
    })

def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def _toast_html(html, title, message, type_='success', status=200):
    """Balas HTML + header X-Toast (dibaca JS untuk showToast)."""
    response = HttpResponse(html, status=status)
    response['X-Toast'] = json.dumps({
        'title': title,
        'message': message,
        'type': type_,
    })
    return response


def _get_transaksi_list(user, status_filter, role):
    """Ambil list transaksi sesuai filter & role."""
    qs = Transaksi.objects.select_related('barang', 'peminjam', 'pemilik')

    if role == 'peminjam':
        qs = qs.filter(peminjam=user)
    else:
        qs = qs.filter(pemilik=user)

    if status_filter == 'berlangsung':
        qs = qs.filter(status__in=[
            'menunggu_verifikasi', 'menunggu_pembayaran',
            'menunggu_konfirmasi', 'disetujui',
        ])
    elif status_filter == 'selesai':
        qs = qs.filter(status='selesai')
    elif status_filter == 'dibatalkan':
        qs = qs.filter(status__in=['dibatalkan', 'ditolak'])

    return qs.order_by('-created_at')

@login_required
@require_POST
def aksi(request, transaksi_id):
    transaksi = get_object_or_404(Transaksi, pk=transaksi_id)
    action = request.POST.get('aksi')

    owner = transaksi.pemilik_id == request.user.pk
    borrower = transaksi.peminjam_id == request.user.pk

    # ===== 1. redirect default (didefinisikan DULU) =====
    if borrower:
        redirect_url = reverse('transaction:riwayat_meminjam')
    elif owner:
        redirect_url = reverse('transaction:permintaan_masuk')
    else:
        redirect_url = reverse('transaction:detail_transaksi', args=[transaksi.id])

    # ===== 2. cek akses =====
    if not (owner or borrower):
        if _is_ajax(request):
            return _toast_html('', 'Gagal', 'Tidak memiliki akses.', 'error', status=403)
        messages.error(request, 'Tidak memiliki akses.')
        return redirect(redirect_url)

    # ===== 3. tabel transisi =====
    transitions = {
        ('menunggu_verifikasi', 'batal', False): ('dibatalkan', 'Peminjam'),
        ('menunggu_verifikasi', 'batal', True):  ('dibatalkan', 'Pemilik'),
        ('menunggu_verifikasi', 'terima', True):     ('menunggu_pembayaran', None),
        ('menunggu_konfirmasi', 'tolak', True):     ('ditolak', None),
        ('menunggu_konfirmasi', 'terima', True):    ('disetujui', None),
        ('disetujui', 'selesai', False):            ('selesai', None),
    }

    result = transitions.get((transaksi.status, action, owner))

    # ===== 4. validasi transisi =====
    if not result:
        if _is_ajax(request):
            return _toast_html('', 'Gagal', 'Aksi tidak tersedia untuk status ini.', 'error', status=400)
        messages.error(request, 'Aksi tidak tersedia untuk status ini.')
        return redirect(redirect_url)

    # ===== 5. validasi selesai sebelum tanggal =====
    if action == 'selesai' and timezone.localdate() < transaksi.tanggal_selesai:
        if _is_ajax(request):
            return _toast_html('', 'Gagal', 'Belum bisa diselesaikan sebelum tanggal selesai.', 'error', status=400)
        messages.error(request, 'Belum bisa diselesaikan sebelum tanggal selesai.')
        return redirect(redirect_url)

    # ===== 6. validasi alasan tolak =====
    alasan = request.POST.get('alasan', '').strip()
    if action == 'tolak' and transaksi.status == 'menunggu_konfirmasi' and not alasan:
        if _is_ajax(request):
            return _toast_html('', 'Gagal', 'Alasan penolakan wajib diisi.', 'error', status=400)
        messages.error(request, 'Alasan penolakan wajib diisi.')
        return redirect(redirect_url)

    # ===== 7. terapkan =====
    transaksi.status = result[0]
    if result[1]:
        transaksi.dibatalkan_oleh = result[1]
        transaksi.dibatalkan_pada = timezone.now()
    if action == 'tolak':
        transaksi.catatan_penolakan = alasan
    transaksi.save()

    pesan = f'Transaksi berhasil diperbarui menjadi "{transaksi.get_status_display()}".'

    # ===== 8. SUKSES: AJAX → HTML partial list + header toast =====
    if _is_ajax(request):
        status_filter = request.POST.get('status_filter', 'semua')
        role = 'peminjam' if borrower else 'pemilik'
        transaksi_list = _get_transaksi_list(request.user, status_filter, role)

        html = render_to_string('partials/transaksi_list.html', {
            'transaksi_list': transaksi_list,
            'is_peminjam': borrower,
            'is_pemilik': owner,
            'status_filter': status_filter,
        }, request=request)

        return _toast_html(html, 'Berhasil', pesan, 'success')

    # ===== 9. SUKSES: form POST biasa → redirect =====
    messages.success(request, pesan)
    return redirect(redirect_url)

# @login_required
# @require_POST
# def aksi(request, transaksi_id):
#     transaksi = get_object_or_404(Transaksi, pk=transaksi_id)
#     action = request.POST.get('aksi')

#     if request.user.pk not in (transaksi.peminjam_id, transaksi.pemilik_id):
#         return _respon_error(request, 'Anda tidak memiliki akses.', redirect_url, status=403)

#     if  transaksi.peminjam_id == request.user.pk:
#         redirect_url = reverse('transaction:riwayat_meminjam')
#     elif transaksi.pemilik_id == request.user.pk:
#         redirect_url = reverse('transaction:permintaan_masuk')
#     else:
#         redirect_url = reverse('transaction:detail_transaksi', args=[transaksi.id])
    
#     # tombol
#     transitions = {
#         ('menunggu_verifikasi', 'batal', False): ('dibatalkan', 'Peminjam'),
#         ('menunggu_verifikasi', 'batal', True):  ('dibatalkan', 'Pemilik'),
#         ('menunggu_verifikasi', 'terima', True):    ('menunggu_pembayaran', None),
#         ('menunggu_konfirmasi', 'tolak', True):     ('ditolak', None),
#         ('menunggu_konfirmasi', 'terima', True):    ('disetujui', None),
#         ('ditolak', 'kirim_ulang', False):          ('menunggu_verifikasi', None),
#     }

#     result = transitions.get((transaksi.status, action,  transaksi.pemilik_id == request.user.pk))

#     if not result:
#         return _respon_error(request, 'Aksi tidak tersedia untuk status ini.', redirect_url, status=403)

#     alasan = request.POST.get('alasan', '').strip()

#     if action == 'tolak' and not alasan:
#         return _respon_error(request, 'Alasan penolakan wajib diisi.', redirect_url)

#     transaksi.status = result[0]
#     if result[1]:
#         transaksi.dibatalkan_oleh = result[1]
#         transaksi.dibatalkan_pada = timezone.now()
#     if action == 'tolak':
#         transaksi.catatan_penolakan = alasan
#     transaksi.save()

#     pesan = f'Transaksi berhasil diperbarui menjadi "{transaksi.get_status_display()}".'
#     return _respon_ok(request, transaksi, pesan, redirect_url)

def edit_bukti(request, transaksi_id):
    transaksi = get_object_or_404(
            Transaksi,
            pk=transaksi_id,
            peminjam=request.user,
            status__in=['menunggu_konfirmasi', 'ditolak']
        )

    file_lama = transaksi.bukti_pembayaran

    if request.method == 'POST':
        form = FormUploadBukti(request.POST, request.FILES, instance=transaksi)
        if form.is_valid():
            transaksi = form.save(commit=False)
            transaksi.status = 'menunggu_konfirmasi'
            transaksi.save()

            if file_lama and file_lama.name != transaksi.bukti_pembayaran.name:
                file_lama.delete(save=False)

                messages.success(request, 'Bukti pembayaran berhasil diperbarui.')
            return redirect('transaction:detail_transaksi', transaksi_id=transaksi.id)
        else:
            # Tampilkan error form, jangan diam-diam
            messages.error(request, 'Gagal menyimpan bukti. Periksa file yang diunggah.')
    else:
        form = FormUploadBukti(instance=transaksi)

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1

    return render(request, 'upload_bukti.html', {
        'form': form,
        'transaksi': transaksi,
        # info_bank : transaksi.profil.bank hrsnya tp blm ada
        "durasi": durasi,
        'is_edit': True,
    })

def update_transaksi_selesai():
    sekarang = timezone.localdate()

    Transaksi.objects.filter(
        status="disetujui",
        tanggal_selesai__lte=sekarang,
    ).update(status="selesai")


