from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_alter_espace_capacite_alter_espace_tarif_horaire_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='espace',
            name='espace_tarif_fixe_100000',
        ),
        migrations.AlterField(
            model_name='espace',
            name='tarif_horaire',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('100000.00'),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal('100000.00'))],
            ),
        ),
        migrations.AddConstraint(
            model_name='espace',
            constraint=models.CheckConstraint(
                check=models.Q(('tarif_horaire__gte', Decimal('100000.00'))),
                name='espace_tarif_min_100000',
            ),
        ),
    ]
