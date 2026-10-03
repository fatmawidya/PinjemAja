from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItemForm
from .models import Item, ItemImage


# Menyimpan tiap file upload jadi satu ItemImage
def _save_images(item, files, start_order=0):
    for offset, f in enumerate(files):
        ItemImage.objects.create(item=item, image=f, order=start_order + offset)


# Semua barang berstatus tersedia. Public (tidak wajib login)
def item_list(request):
    items = Item.objects.filter(status='tersedia').prefetch_related('images')
    return render(request, 'items/item_list.html', {'items': items})


# Detail satu barang. Info kontak pemilik disembunyikan di template kalau belum login
def item_detail(request, pk):
    item = get_object_or_404(
        Item.objects.prefetch_related('images'), pk=pk
    )
    return render(request, 'items/item_detail.html', {
        'item': item,
        'is_owner': request.user == item.owner,
    })


# owner di-set otomatis
@login_required
def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user   
            item.save()
            _save_images(item, form.cleaned_data['images'])
            messages.success(request, 'Barang berhasil ditambahkan.')
            return redirect('items:item_detail', pk=item.pk)
    else:
        form = ItemForm()
    return render(request, 'items/item_form.html', {'form': form, 'mode': 'create'})


# hanya owner yang boleh edit
@login_required
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied  

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            # foto baru ditambahkan setelah foto yang sudah ada
            _save_images(item, form.cleaned_data['images'],
                         start_order=item.images.count())
            messages.success(request, 'Barang berhasil diperbarui.')
            return redirect('items:item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'items/item_form.html', {
        'form': form, 'mode': 'update', 'item': item,
    })


# hanya owner yang boleh hapus
@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied 

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Barang berhasil dihapus.')
        return redirect('items:my_items')
    return render(request, 'items/item_confirm_delete.html', {'item': item})


# Barang milik user yang sedang login
@login_required
def my_items(request):
    items = Item.objects.filter(owner=request.user).prefetch_related('images')
    return render(request, 'items/my_items.html', {'items': items})