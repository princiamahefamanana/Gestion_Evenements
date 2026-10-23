from django.db import migrations, models


def mark_existing_payments_as_received(apps, schema_editor):
    Paiement = apps.get_model('booking', 'Paiement')
    Paiement.objects.all().update(envoye_admin=True)


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_alter_reservation_nombre_invites'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiement',
            name='envoye_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_existing_payments_as_received, migrations.RunPython.noop),
    ]
