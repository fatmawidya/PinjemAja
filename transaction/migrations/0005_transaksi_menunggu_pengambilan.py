from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0004_transaksi_harga_terkunci'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaksi',
            name='status',
            field=models.CharField(
                choices=[
                    ('menunggu_verifikasi', 'Menunggu Verifikasi'),
                    ('menunggu_pembayaran', 'Menunggu Pembayaran'),
                    ('menunggu_pengambilan', 'Menunggu Pengambilan / Pembayaran COD'),
                    ('menunggu_konfirmasi', 'Menunggu Konfirmasi'),
                    ('ditolak', 'Ditolak'),
                    ('disetujui', 'Sedang Berlangsung'),
                    ('selesai', 'Selesai'),
                    ('dibatalkan', 'Dibatalkan'),
                ],
                default='menunggu_verifikasi',
                max_length=30,
            ),
        ),
    ]
