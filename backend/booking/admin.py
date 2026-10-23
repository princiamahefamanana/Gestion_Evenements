from django.contrib import admin

from .models import Client, Espace, Paiement, Reservation, TypeEvenement

admin.site.register([Client, Espace, TypeEvenement, Reservation, Paiement])
