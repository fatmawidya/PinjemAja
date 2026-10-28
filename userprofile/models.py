from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

PAYMENT_PROVIDERS = [
    ('', 'Pilih metode...'),
    ('BCA', 'BCA'), ('BRI', 'BRI'), ('BNI', 'BNI'), ('Mandiri', 'Mandiri'),
    ('OVO', 'OVO'), ('GoPay', 'GoPay'), ('DANA', 'DANA'), ('ShopeePay', 'ShopeePay'),
]
EWALLETS = {'OVO', 'GoPay', 'DANA', 'ShopeePay'}

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)          # kota/kabupaten
    district = models.CharField(max_length=100, blank=True)      # kecamatan
    subdistrict = models.CharField(max_length=100, blank=True)   # kelurahan
    street_address = models.TextField(blank=True)                # alamat jalan detail
    bio = models.TextField(blank=True)
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDERS, blank=True)
    payment_number = models.CharField(max_length=20, blank=True)
    payment_holder = models.CharField(max_length=100, blank=True)

    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    rating = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    @property
    def is_ewallet(self):
        return self.payment_provider in EWALLETS

    @property
    def has_payment_info(self):
        return bool(self.payment_provider and self.payment_number and self.payment_holder)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)