
from decimal import Decimal
import django.core.validators
from django.db import migrations, models


def set_fixed_hourly_rate(apps, schema_editor):
    Espace = apps.get_model('booking', 'Espace')
    Espace.objects.using(schema_editor.connection.alias).all().update(
        tarif_horaire=Decimal('100000.00'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_remove_eventmanager_legacy_tables'),
    ]

    operations = [
        migrations.RunPython(set_fixed_hourly_rate, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='espace',
            name='capacite',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(80)]),
        ),
        migrations.AlterField(
            model_name='espace',
            name='tarif_horaire',
            field=models.DecimalField(decimal_places=2, default=Decimal('100000.00'), editable=False, max_digits=12),
        ),
        migrations.AddConstraint(
            model_name='espace',
            constraint=models.CheckConstraint(check=models.Q(('capacite__gte', 80)), name='espace_capacite_min_80'),
        ),
        migrations.AddConstraint(
            model_name='espace',
            constraint=models.CheckConstraint(check=models.Q(('tarif_horaire', Decimal('100000.00'))), name='espace_tarif_fixe_100000'),
        ),
    ]
