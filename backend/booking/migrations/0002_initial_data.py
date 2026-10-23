from django.db import migrations


def create_default_types(apps, schema_editor):
    TypeEvenement = apps.get_model('booking', 'TypeEvenement')
    Client = apps.get_model('booking', 'Client')
    User = apps.get_model('accounts', 'User')
    types = [
        ('Mariage', 'Cérémonies et réceptions de mariage.'),
        ('Anniversaire', 'Fêtes et réceptions d’anniversaire.'),
        ('Conférence', 'Conférences et rencontres professionnelles.'),
    ]
    for nom, description in types:
        TypeEvenement.objects.using(schema_editor.connection.alias).get_or_create(
            nom=nom,
            defaults={'description': description},
        )

    seen_emails = set()
    for user in User.objects.using(schema_editor.connection.alias).exclude(email='').order_by('pk'):
        normalized_email = user.email.casefold()
        if normalized_email in seen_emails:
            continue
        seen_emails.add(normalized_email)
        Client.objects.using(schema_editor.connection.alias).get_or_create(
            user_id=user.pk,
            defaults={
                'nom': f'{user.first_name} {user.last_name}'.strip() or user.username,
                'email': user.email,
                'telephone': user.phone,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_alter_user_table'),
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_types, migrations.RunPython.noop),
    ]
