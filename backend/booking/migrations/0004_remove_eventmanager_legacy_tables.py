from django.db import migrations


LEGACY_APP_LABELS = (
    'events',
    'participants',
    'registrations',
    'venues',
    'payments',
    'tickets',
    'reports',
)

LEGACY_TABLES = (
    'payments_refund',
    'payments_payment',
    'tickets_ticket',
    'registrations_registration',
    'events_event',
    'participants_participant',
    'venues_venue',
)


def remove_eventmanager_legacy_data(apps, schema_editor):
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        for table_name in LEGACY_TABLES:
            cursor.execute(f'DROP TABLE IF EXISTS {quote_name(table_name)}')

    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.using(connection.alias).filter(
        app_label__in=LEGACY_APP_LABELS,
    ).delete()

    with connection.cursor() as cursor:
        cursor.execute(
            f'DELETE FROM {quote_name("django_migrations")} '
            f'WHERE {quote_name("app")} IN ({", ".join(["%s"] * len(LEGACY_APP_LABELS))})',
            LEGACY_APP_LABELS,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('booking', '0003_alter_espace_capacite_alter_espace_tarif_horaire'),
    ]

    operations = [
        migrations.RunPython(remove_eventmanager_legacy_data),
    ]
