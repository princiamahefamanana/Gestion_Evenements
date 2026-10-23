
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_alter_client_telephone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='nombre_invites',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(10)]),
        ),
    ]
