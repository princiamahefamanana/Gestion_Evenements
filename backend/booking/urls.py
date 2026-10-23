from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ClientViewSet,
    EspaceViewSet,
    PaiementViewSet,
    ReservationViewSet,
    TypeEvenementViewSet,
    dashboard_view,
)

router = DefaultRouter()
router.register('clients', ClientViewSet, basename='client')
router.register('espaces', EspaceViewSet, basename='espace')
router.register('types-evenements', TypeEvenementViewSet, basename='type-evenement')
router.register('reservations', ReservationViewSet, basename='reservation')
router.register('paiements', PaiementViewSet, basename='paiement')

urlpatterns = [
    path('tableau-de-bord/', dashboard_view, name='booking-dashboard'),
    *router.urls,
]
