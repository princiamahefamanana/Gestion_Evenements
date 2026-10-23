

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('telephone', models.CharField(blank=True, default='', max_length=30)),
                ('cree_le', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'clients',
                'ordering': ['nom', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Espace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('adresse', models.CharField(max_length=255)),
                ('capacite', models.PositiveIntegerField()),
                ('tarif_horaire', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('description', models.TextField(blank=True, default='')),
                ('disponible', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'espaces',
                'ordering': ['nom', 'id'],
            },
        ),
        migrations.CreateModel(
            name='TypeEvenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'type d’événement',
                'verbose_name_plural': 'types d’événements',
                'db_table': 'types_evenements',
                'ordering': ['nom', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField()),
                ('nombre_invites', models.PositiveIntegerField()),
                ('statut', models.CharField(choices=[('pending', 'En attente'), ('confirmed', 'Confirmée'), ('cancelled', 'Annulée'), ('completed', 'Terminée')], default='pending', max_length=20)),
                ('montant_total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('cree_le', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='booking.client')),
                ('espace', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='booking.espace')),
                ('type_evenement', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='booking.typeevenement')),
            ],
            options={
                'db_table': 'reservations',
                'ordering': ['-date_debut', '-id'],
            },
        ),
        migrations.CreateModel(
            name='Paiement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant', models.DecimalField(decimal_places=2, max_digits=12)),
                ('mode_paiement', models.CharField(choices=[('cash', 'Espèces'), ('transfer', 'Virement'), ('card', 'Carte bancaire')], default='cash', max_length=20)),
                ('statut', models.CharField(choices=[('pending', 'En attente'), ('paid', 'Payé'), ('cancelled', 'Annulé')], default='pending', max_length=20)),
                ('reference', models.CharField(blank=True, default='', max_length=100)),
                ('date_paiement', models.DateTimeField(auto_now_add=True)),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='paiements', to='booking.reservation')),
            ],
            options={
                'db_table': 'paiements',
                'ordering': ['-date_paiement', '-id'],
            },
        ),
    ]
