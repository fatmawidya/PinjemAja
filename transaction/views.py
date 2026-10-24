from datetime import date

from django.http import JsonResponse
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
    
# @login_required
def riwayat_meminjam(request):
    transaksi_list = (Transaksi.objects.filter(peminjam=request.user).select_related('barang', 'pemilik').order_by('-created_at'))
    
    status_filter = request.GET.get("status", "semua")
    status_map = {
        "berlangsung": [
            "menunggu_verifikasi",
            "menunggu_pembayaran",
            "menunggu_konfirmasi",
            "disetujui" ],
        "selesai": ["selesai"],
        "dibatalkan": [
            "dibatalkan",
            "ditolak",
        ],
    }

    if status_filter in status_map:
        transaksi_list = transaksi_list.filter(status__in=status_map[status_filter])

    context = {
        "transaksi_list": transaksi_list,
        "status_filter": status_filter,
    }

    return render(request, "riwayat_meminjam.html", context)
    
# @login_required
def permintaan_masuk(request):
    transaksi_list = (Transaksi.objects.filter(pemilik=request.user).select_related("barang", "peminjam",).order_by("-created_at"))
    status_filter = request.GET.get("status", "semua")
    status_map = {
            "berlangsung": [
                "menunggu_verifikasi",
                "menunggu_pembayaran",
                "menunggu_konfirmasi",
                "disetujui" ],
            "selesai": ["selesai"],
            "dibatalkan": [
                "dibatalkan",
                "ditolak",
            ],
        }
    
    if status_filter in status_map:
        transaksi_list = transaksi_list.filter(status__in=status_map[status_filter])

    context = {
        "transaksi_list": transaksi_list,
        "status_filter": status_filter,
    }

    return render(request, "permintaan_masuk.html", context)

# @login_required
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
    })

# @login_required
def detail_transaksi(request, transaksi_id):
    transaksi = get_object_or_404 (Transaksi.objects.select_related("barang", "peminjam", "pemilik"), pk=transaksi_id)

    if request.user.pk not in (transaksi.peminjam_id, transaksi.pemilik_id):
        messages.error(request, "Anda tidak memiliki akses.")
        return redirect("transaction:riwayat_meminjam")

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1
    return render(request, "detail_transaksi.html", {
        "transaksi": transaksi,
        "durasi": durasi,
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

    return render(request, 'form_pinjam.html', {
        'form': form,
        'transaksi': transaksi,
        'barang': transaksi.barang,
        'is_edit': True,
    })

@login_required
@require_POST
def aksi(request, transaksi_id):
    transaksi = get_object_or_404(Transaksi, pk=transaksi_id)
    action = request.POST.get('aksi')

    if request.user.pk not in (transaksi.peminjam_id, transaksi.pemilik_id):
        messages.error(request, 'Anda tidak memiliki akses.')
        return redirect('transaction:detail_transaksi', transaksi_id=transaksi.id)

    if transaksi.peminjam_id:
        redirect_url = reverse('transaction:riwayat_meminjam')
    elif transaksi.pemilik_id:
        redirect_url = reverse('transaction:permintaan_masuk')
    else:
        redirect_url = reverse('transaction:detail_transaksi', args=[transaksi.id])
    
    # tombol
    transitions = {
        ('menunggu_verifikasi', 'batal', False): ('dibatalkan', 'Peminjam'),
        ('menunggu_verifikasi', 'batal', True):  ('dibatalkan', 'Pemilik'),
        ('menunggu_verifikasi', 'terima', True):    ('menunggu_pembayaran', None),
        ('menunggu_konfirmasi', 'tolak', True):     ('ditolak', None),
        ('menunggu_konfirmasi', 'terima', True):    ('disetujui', None),
        ('ditolak', 'kirim_ulang', False):          ('menunggu_verifikasi', None),
    }

    result = transitions.get((transaksi.status, action, transaksi.pemilik_id))

    if not result:
        messages.error(request, 'Aksi tidak tersedia untuk status ini.')
        return redirect(redirect_url)

    alasan = request.POST.get('alasan', '').strip()
    if action == 'tolak' and not alasan:
        messages.error(request, 'Alasan penolakan wajib diisi.')
        return redirect(redirect_url)

    transaksi.status = result[0]
    if result[1]:
        transaksi.dibatalkan_oleh = result[1]
        transaksi.dibatalkan_pada = timezone.now()
    if action == 'tolak':
        transaksi.catatan_penolakan = alasan
    transaksi.save()

    messages.success(request, f'Transaksi berhasil diperbarui menjadi "{transaksi.get_status_display()}".')
    return redirect(redirect_url)

def edit_bukti(request, transaksi_id):
    transaksi = get_object_or_404(
            Transaksi,
            pk=transaksi_id,
            peminjam=request.user,
            status='menunggu_konfirmasi',
        )

    if request.method == 'POST':
        form = FormUploadBukti(request.POST, request.FILES, instance=transaksi)
        if form.is_valid():
            transaksi= form.save()
            messages.success(request, 'Bukti pembayaran berhasil diperbarui.')
            return redirect('transaction:detail_transaksi', transaksi_id=transaksi.id)

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
    


