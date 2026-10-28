import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile


class ProfileModelTest(TestCase):
    def test_profile_auto_created_on_user_creation(self):
        """Profile harus otomatis terbuat lewat signal saat User baru dibuat."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str_representation(self):
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = Profile.objects.get(user=user)
        self.assertEqual(str(profile), 'testuser')

    def test_profile_default_rating_is_zero(self):
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.rating, 0)


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('userprofile:register')

    def test_register_page_accessible(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # pastikan user langsung login setelah register
        response = self.client.get(reverse('userprofile:my_profile'))
        self.assertEqual(response.status_code, 200)

    def test_register_fails_with_mismatched_passwords(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser2',
            'email': 'new2@test.com',
            'password1': 'ComplexPass123',
            'password2': 'DifferentPass456',
        })
        self.assertEqual(response.status_code, 200)  # form error, tidak redirect
        self.assertFalse(User.objects.filter(username='newuser2').exists())

    def test_register_fails_with_duplicate_username(self):
        User.objects.create_user(username='existinguser', password='pass123')
        response = self.client.post(self.register_url, {
            'username': 'existinguser',
            'email': 'dup@test.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        })
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.login_url = reverse('userprofile:login')

    def test_login_page_accessible(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_success_with_correct_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser', 'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # tetap di halaman login
        self.assertContains(response, 'correct username and password')  # pesan error django default, sesuaikan jika custom


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_logout_redirects_and_clears_session(self):
        response = self.client.get(reverse('userprofile:logout'))
        self.assertEqual(response.status_code, 302)
        # setelah logout, akses halaman yang butuh login harus ditolak
        response = self.client.get(reverse('userprofile:my_profile'))
        self.assertEqual(response.status_code, 302)


class AuthorizationTest(TestCase):
    """Test khusus untuk memastikan filter berbasis autentikasi bekerja."""

    def setUp(self):
        self.client = Client()

    def test_my_profile_requires_login(self):
        response = self.client.get(reverse('userprofile:my_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/profile/login/', response.url)

    def test_edit_profile_requires_login(self):
        response = self.client.get(reverse('userprofile:edit_profile'))
        self.assertEqual(response.status_code, 302)

    def test_public_profile_requires_login(self):
        user = User.objects.create_user(username='someoneelse', password='pass123')
        response = self.client.get(reverse('userprofile:public_profile', args=[user.id]))
        self.assertEqual(response.status_code, 302)

    def test_public_profile_does_not_expose_sensitive_fields(self):
        owner = User.objects.create_user(username='owner', password='pass123')
        profile = Profile.objects.get(user=owner)
        profile.phone_number = '08123456789'
        profile.city = 'Jakarta Selatan'
        profile.district = 'Kebayoran Baru'
        profile.subdistrict = 'Gandaria'
        profile.street_address = 'Jl. Rahasia No. 1'
        profile.save()

        viewer = User.objects.create_user(username='viewer', password='pass123')
        self.client.login(username='viewer', password='pass123')
        response = self.client.get(reverse('userprofile:public_profile', args=[owner.id]))

        self.assertNotContains(response, '08123456789')
        self.assertContains(response, 'Jakarta Selatan')
        self.assertNotContains(response, 'Kebayoran Baru')
        self.assertNotContains(response, 'Gandaria')
        self.assertNotContains(response, 'Jl. Rahasia No. 1')

class EditProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        self.edit_url = reverse('userprofile:edit_profile')

    def test_edit_profile_page_accessible_when_logged_in(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_updates_data(self):
        response = self.client.post(self.edit_url, {
            'phone_number': '08123456789',
            'city': 'Jakarta Selatan',
            'bio': 'Halo, saya pengguna PinjemAja',
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, '08123456789')
        self.assertEqual(self.user.profile.city, 'Jakarta Selatan')
        self.assertEqual(self.user.profile.bio, 'Halo, saya pengguna PinjemAja')
        
    def test_edit_profile_only_affects_own_profile(self):
        """User A tidak boleh bisa mengubah profile User B lewat endpoint edit."""
        other_user = User.objects.create_user(username='otheruser', password='pass123')
        other_profile_before = other_user.profile.bio

        self.client.post(self.edit_url, {
            'phone_number': '0899999999',
            'address': 'Bandung',
            'bio': 'Mencoba mengubah profil sendiri',
        })

        other_user.profile.refresh_from_db()
        self.assertEqual(other_user.profile.bio, other_profile_before)  # tidak berubah


class PublicProfileViewTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.viewer = User.objects.create_user(username='viewer', password='pass123')
        self.client = Client()
        self.client.login(username='viewer', password='pass123')

    def test_public_profile_shows_correct_user(self):
        response = self.client.get(reverse('userprofile:public_profile', args=[self.owner.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner.username)

    def test_public_profile_404_for_nonexistent_user(self):
        response = self.client.get(reverse('userprofile:public_profile', args=[9999]))
        self.assertEqual(response.status_code, 404)


class RegisterHtmxViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('userprofile:register_htmx')

    def test_register_htmx_success_returns_204_with_redirect_header(self):
        response = self.client.post(self.url, {
            'username': 'htmxuser',
            'email': 'htmx@test.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        })
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)
        self.assertTrue(User.objects.filter(username='htmxuser').exists())

    def test_register_htmx_failure_rerenders_form_with_error_trigger(self):
        response = self.client.post(self.url, {
            'username': 'htmxuser2',
            'email': 'htmx2@test.com',
            'password1': 'ComplexPass123',
            'password2': 'WrongPass456',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        trigger_data = json.loads(response.headers['HX-Trigger'])
        self.assertEqual(trigger_data['showToast']['type'], 'error')
        self.assertFalse(User.objects.filter(username='htmxuser2').exists())


class LoginHtmxViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.url = reverse('userprofile:login_htmx')

    def test_login_htmx_success_returns_204_with_redirect_header(self):
        response = self.client.post(self.url, {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)

    def test_login_htmx_failure_rerenders_form_with_error_trigger(self):
        response = self.client.post(self.url, {
            'username': 'testuser', 'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        trigger_data = json.loads(response.headers['HX-Trigger'])
        self.assertEqual(trigger_data['showToast']['type'], 'error')


class EditProfileHtmxViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile:edit_profile_htmx')

    def test_edit_profile_htmx_requires_login(self):
        self.client.logout()
        response = self.client.post(self.url, {'phone_number': '0812'})
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_htmx_success_updates_data_and_redirects(self):
        response = self.client.post(self.url, {
            'phone_number': '08123456789',
            'bio': 'Halo dari HTMX',
        })
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers['HX-Redirect'], reverse('userprofile:my_profile'))

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, '08123456789')
        self.assertEqual(self.user.profile.bio, 'Halo dari HTMX')

    def test_edit_profile_htmx_invalid_data_triggers_error_toast(self):
        response = self.client.post(self.url, {
            'phone_number': 'x' * 300,  # melebihi max_length=20
            'bio': 'test',
        })
        self.assertEqual(response.status_code, 200)
        trigger_data = json.loads(response.headers['HX-Trigger'])
        self.assertEqual(trigger_data['showToast']['type'], 'error')