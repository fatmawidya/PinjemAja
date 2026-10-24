from datetime import date

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone

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
    transaksi_list = (Transaksi.objects.filter(pemilik=request.user).select_related("barang", "peminjam").order_by("-created_at"))
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


