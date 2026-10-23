
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0006_space_tariff_minimum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='telephone',
            field=models.CharField(blank=True, default='', max_length=30, validators=[django.core.validators.RegexValidator('^\\d{10}$', 'Le téléphone doit contenir exactement 10 chiffres.')]),
        ),
    ]
