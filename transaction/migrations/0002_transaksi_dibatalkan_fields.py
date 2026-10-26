from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('transaction', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='transaksi',
            name='dibatalkan_oleh',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='transaksi',
            name='dibatalkan_pada',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
