# Generated migration for adding payment_status field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('NONE', 'None'),
                    ('PENDING', 'Pending'),
                    ('PAID', 'Paid'),
                    ('NOT_REQUIRED', 'Not Required'),
                ],
                default='NONE',
                help_text='Payment status separate from article scientific workflow',
                max_length=20
            ),
        ),
    ]

