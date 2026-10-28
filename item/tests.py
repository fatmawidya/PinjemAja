from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from item.models import Item
from item.forms import ItemForm, MAX_PRICE
from transaction.models import Transaksi

class SimpleItemTest(TestCase):
    def setUp(self):
        # Setup data dasar
        self.client = Client()
        self.owner = User.objects.create_user(username='jihyo', password='password123')
        self.other_user = User.objects.create_user(username='tzuyu', password='password123')
        
        self.item = Item.objects.create(
            owner=self.owner, 
            name='Kamera Fujifilm', 
            description='Kamera bagus',
            category='fotografi', 
            price=Decimal('50000.00'), 
            condition='baik', 
            location='Depok'
        )

    # ==========================================
    # 1. TEST MODEL & STATUS DINAMIS
    # ==========================================
    def test_status_tersedia(self):
        """Cek status default jika tidak ada transaksi"""
        self.assertEqual(self.item.display_status, 'tersedia')

    def test_status_pending(self):
        """Cek status jadi 'pending' jika ada transaksi menunggu"""
        Transaksi.objects.create(
            barang=self.item, peminjam=self.other_user, pemilik=self.owner,
            tanggal_mulai='2026-10-01', tanggal_selesai='2026-10-05', status='menunggu_verifikasi'
        )
        self.assertEqual(self.item.display_status, 'pending')

    def test_status_dipinjam(self):
        """Cek status jadi 'dipinjam' jika transaksi disetujui"""
        Transaksi.objects.create(
            barang=self.item, peminjam=self.other_user, pemilik=self.owner,
            tanggal_mulai='2026-10-01', tanggal_selesai='2026-10-05', status='disetujui'
        )
        self.assertEqual(self.item.display_status, 'dipinjam')

    # ==========================================
    # 2. TEST FORM VALIDATION (HARGA)
    # ==========================================
    def test_form_harga_valid(self):
        """Form valid jika harga berupa angka normal"""
        form = ItemForm(data={
            'name': 'Tenda', 'description': 'Tenda 4 orang', 'category': 'camping',
            'price': '150000', 'condition': 'baik', 'location': 'Bogor'
        })
        self.assertTrue(form.is_valid())

    def test_form_harga_nol(self):
        """Form tidak valid jika harga 0"""
        form = ItemForm(data={
            'name': 'Tenda', 'description': 'Tenda', 'category': 'camping',
            'price': '0', 'condition': 'baik', 'location': 'Bogor'
        })
        self.assertFalse(form.is_valid())

    def test_form_harga_terlalu_mahal(self):
        """Form tidak valid jika harga melebihi batas MAX_PRICE"""
        form = ItemForm(data={
            'name': 'Tenda', 'description': 'Tenda', 'category': 'camping',
            'price': str(MAX_PRICE + 1), 'condition': 'baik', 'location': 'Bogor'
        })
        self.assertFalse(form.is_valid())

    # ==========================================
    # 3. TEST VIEWS & AKSES (HAK AKSES)
    # ==========================================
    def test_halaman_detail_bisa_diakses(self):
        """Halaman detail barang bisa diakses publik"""
        response = self.client.get(reverse('item:item_detail', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kamera Fujifilm')

    def test_halaman_tambah_barang_wajib_login(self):
        """User anonim tidak bisa buka form tambah barang"""
        response = self.client.get(reverse('item:item_create'))
        self.assertEqual(response.status_code, 302) # Redirect ke login

    def test_owner_bisa_edit_barang(self):
        """Owner bisa membuka halaman edit barangnya"""
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:item_update', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_orang_lain_tidak_bisa_edit_barang(self):
        """User lain (bukan owner) akan ditolak (403) jika coba edit"""
        self.client.login(username='tzuyu', password='password123')
        response = self.client.get(reverse('item:item_update', args=[self.item.pk]))
        self.assertEqual(response.status_code, 403) # Permission Denied

    def test_owner_bisa_hapus_barang(self):
        """Owner bisa menghapus barangnya"""
        self.client.login(username='jihyo', password='password123')
        response = self.client.post(reverse('item:item_delete', args=[self.item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists()) # Barang hilang dari DB

    def test_halaman_my_items_hanya_milik_sendiri(self):
        """Halaman etalase saya hanya menampilkan barang milik user yang login"""
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:my_items'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kamera Fujifilm')