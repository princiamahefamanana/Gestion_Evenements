
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=30, validators=[django.core.validators.RegexValidator('^\\d{10}$', 'Le téléphone doit contenir exactement 10 chiffres.')]),
        ),
    ]
