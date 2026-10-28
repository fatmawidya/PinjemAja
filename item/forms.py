from decimal import Decimal

from django import forms
from django.core.validators import RegexValidator

from .models import Item

MAX_IMAGES = 5
MAX_IMAGE_SIZE = 5 * 1024 * 1024  
MAX_PRICE = 99_999_999  


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


# File yang selain gambar (misal .exe / .html yang diganti nama jadi .jpg) ditolak.
class MultipleImageField(forms.ImageField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)] if data else []


class ItemForm(forms.ModelForm):
    price = forms.CharField(
        label='Harga sewa per hari',
        widget=forms.TextInput(attrs={
            'placeholder': 'Masukkan angka saja (contoh: 50000)',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'off',
        }),
        validators=[RegexValidator(
            r'\A[0-9]+\Z', 'Masukkan angka saja, tanpa titik atau koma.',
        )],
    )

    images = MultipleImageField(
        required=False,
        label='Foto barang',
        help_text='Bisa pilih lebih dari satu foto (maks. 5 foto, 5 MB per foto). '
                  'Foto pertama jadi sampul.',
    )

    class Meta:
        model = Item
        fields = ['name', 'description', 'category', 'price', 'condition', 'location']
        labels = {
            'name': 'Nama barang',
            'description': 'Deskripsi',
            'category': 'Kategori',
            'price': 'Harga sewa per hari',
            'condition': 'Kondisi',
            'location': 'Dikirim dari kota',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.price is not None:
            self.initial['price'] = int(self.instance.price)

    def clean_price(self):
        price = Decimal(self.cleaned_data['price'])
        if price <= 0:
            raise forms.ValidationError('Harga harus lebih dari 0.')
        if price > MAX_PRICE:
            raise forms.ValidationError('Harga terlalu besar (maksimal 99.999.999).')
        return price

    def clean_images(self):
        images = self.cleaned_data.get('images') or []
        if len(images) > MAX_IMAGES:
            raise forms.ValidationError(f'Maksimal {MAX_IMAGES} foto sekali upload.')
        for img in images:
            if img.size > MAX_IMAGE_SIZE:
                raise forms.ValidationError(
                    f'Ukuran "{img.name}" lebih dari 5 MB.'
                )
        return images