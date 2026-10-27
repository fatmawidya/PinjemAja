from django import forms
from item.models import Item


class SearchForm(forms.Form):
    """
    Form untuk menyaring barang pada Modul Pencarian & Filter (Celine).
    Sesuai dengan spesifikasi dokumen proposal kelompok PBP A08 (Halaman 24).
    """
    keyword = forms.CharField(
        max_length=255,
        required=False,
        label='Kata Kunci',
        widget=forms.TextInput(attrs={
            'placeholder': 'Cari nama barang...',
            'id': 'search-input-field',
            'autocomplete': 'off',
        })
    )
    category = forms.ChoiceField(
        choices=[('', 'Semua Kategori')] + Item.CATEGORY_CHOICES,
        required=False,
        label='Kategori',
        widget=forms.Select(attrs={'class': 'custom-select'})
    )
    location = forms.CharField(
        max_length=255,
        required=False,
        label='Lokasi Kota',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ketik nama kota...',
            'id': 'location-text-input',
            'autocomplete': 'off',
        })
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        label='Harga Minimum',
        widget=forms.NumberInput(attrs={'placeholder': 'Min', 'id': 'min-price-input'})
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        label='Harga Maksimum',
        widget=forms.NumberInput(attrs={'placeholder': 'Maks', 'id': 'max-price-input'})
    )
    sort = forms.ChoiceField(
        choices=[
            ('latest', 'Terbaru'),
            ('price_asc', 'Harga: Termurah'),
            ('price_desc', 'Harga: Termahal'),
            ('name_asc', 'Nama (A - Z)'),
        ],
        required=False,
        label='Urutkan',
        widget=forms.Select(attrs={'class': 'custom-select', 'id': 'sort-select'})
    )
