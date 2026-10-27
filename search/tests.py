from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from item.models import Item
from search.models import SearchHistory

User = get_user_model()


class SearchModuleTests(TestCase):
    """
    Unit Test untuk Modul Pencarian & Filter (Celine).
    Memastikan halaman search, filter AJAX JSON, dan CRUD SearchHistory berjalan 100%.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testceline', password='password123')
        self.item1 = Item.objects.create(
            name='Tenda Dome Eiger',
            description='Tenda camping tahan hujan kapasitas 4 orang',
            category='camping',
            owner=self.user,
            price=50000,
            location='Bandung',
            status='tersedia'
        )
        self.item2 = Item.objects.create(
            name='Kamera Sony A7III',
            description='Kamera mirrorless fotografi profesional',
            category='fotografi',
            owner=self.user,
            price=200000,
            location='Jakarta Selatan',
            status='tersedia'
        )

    def test_search_page_status_code(self):
        """Memastikan halaman /search/ dapat diakses dengan kode 200."""
        response = self.client.get(reverse('search:search_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/search.html')

    def test_search_api_returns_json(self):
        """Memastikan endpoint /search/api/ mengembalikan format data JSON yang benar."""
        response = self.client.get(reverse('search:search_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 2)

    def test_filter_by_keyword(self):
        """Memastikan fitur pencarian kata kunci menyaring barang dengan akurat."""
        response = self.client.get(reverse('search:search_api'), {'q': 'kamera'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['name'], 'Kamera Sony A7III')

    def test_filter_by_category(self):
        """Memastikan filter kategori berfungsi."""
        response = self.client.get(reverse('search:search_api'), {'category': 'camping'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['name'], 'Tenda Dome Eiger')

    def test_filter_by_location(self):
        """Memastikan filter lokasi kota berfungsi."""
        response = self.client.get(reverse('search:search_api'), {'location': 'Bandung'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['location'], 'Bandung')

    def test_search_history_crud(self):
        """Memastikan riwayat pencarian (Create, Read, Delete) bekerja normal."""
        # Create
        self.client.get(reverse('search:search_api'), {'q': 'tenda'})
        self.assertTrue(SearchHistory.objects.filter(keyword='tenda').exists())

        # Delete
        history = SearchHistory.objects.get(keyword='tenda')
        res_del = self.client.post(reverse('search:delete_search_history', args=[history.pk]))
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(SearchHistory.objects.filter(keyword='tenda').exists())
