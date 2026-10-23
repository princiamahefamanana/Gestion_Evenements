from rest_framework import permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import CharField, Q
from django.db.models.functions import Cast

from .models import Client, Espace, Paiement, Reservation, TypeEvenement
from .serializers import (
    ClientSerializer,
    EspaceSerializer,
    PaiementSerializer,
    ReservationSerializer,
    TypeEvenementSerializer,
)


def is_staff_user(user):
    return user.is_superuser or user.role in ['admin', 'organizer']


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        clients = Client.objects.select_related('user').all()
        if is_staff_user(self.request.user):
            queryset = clients
        else:
            queryset = clients.filter(user=self.request.user)
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.filter(Q(nom__icontains=query) | Q(email__icontains=query) | Q(telephone__icontains=query))
        return queryset.order_by('nom')

    def perform_create(self, serializer):
        raise PermissionDenied('Les clients créent leur compte eux-mêmes avant de réserver un espace.')

    def perform_update(self, serializer):
        client = self.get_object()
        if is_staff_user(self.request.user):
            raise PermissionDenied('L’équipe ne peut pas modifier les informations personnelles des clients.')
        if client.user_id != self.request.user.id:
            raise PermissionDenied('Vous ne pouvez modifier que votre propre profil client.')
        serializer.save()

    def perform_destroy(self, instance):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut supprimer les clients.')
        try:
            instance.delete()
        except ProtectedError as error:
            raise ValidationError(
                'Ce client possède des réservations et ne peut pas être supprimé.'
            ) from error


class EspaceViewSet(viewsets.ModelViewSet):
    queryset = Espace.objects.all().order_by('nom')
    serializer_class = EspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Espace.objects.all()
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.annotate(
                search_capacity=Cast('capacite', output_field=CharField()),
                search_hourly_rate=Cast('tarif_horaire', output_field=CharField()),
            ).filter(
                Q(nom__icontains=query)
                | Q(adresse__icontains=query)
                | Q(description__icontains=query)
                | Q(search_capacity__icontains=query)
                | Q(search_hourly_rate__icontains=query)
            )
        return queryset.order_by('nom')

    def perform_create(self, serializer):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut gérer les espaces.')
        serializer.save()

    def perform_update(self, serializer):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut gérer les espaces.')
        serializer.save()

    def perform_destroy(self, instance):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut gérer les espaces.')
        instance.delete()


class TypeEvenementViewSet(viewsets.ModelViewSet):
    queryset = TypeEvenement.objects.all().order_by('nom')
    serializer_class = TypeEvenementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TypeEvenement.objects.all()
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.filter(Q(nom__icontains=query) | Q(description__icontains=query))
        return queryset.order_by('nom')

    def perform_create(self, serializer):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut gérer les types d’événement.')
        serializer.save()

    def perform_update(self, serializer):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut gérer les types d’événement.')
        serializer.save()

    def perform_destroy(self, instance):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut gérer les types d’événement.')
        instance.delete()


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        reservations = Reservation.objects.select_related('client', 'espace', 'type_evenement')
        if is_staff_user(self.request.user):
            queryset = reservations
        else:
            queryset = reservations.filter(client__user=self.request.user)
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.annotate(
                search_start=Cast('date_debut', output_field=CharField()),
                search_end=Cast('date_fin', output_field=CharField()),
            ).filter(
                Q(client__nom__icontains=query)
                | Q(client__email__icontains=query)
                | Q(espace__nom__icontains=query)
                | Q(type_evenement__nom__icontains=query)
                | Q(statut__icontains=query)
                | Q(search_start__icontains=query)
                | Q(search_end__icontains=query)
            )
        return queryset

    def perform_create(self, serializer):
        if is_staff_user(self.request.user):
            if 'client' not in serializer.validated_data:
                raise ValidationError({'client': 'Sélectionnez un client pour cette réservation.'})
            serializer.save(statut=Reservation.STATUS_PENDING)
            return
        requested_client = serializer.validated_data.get('client')
        if requested_client and requested_client.user_id != self.request.user.id:
            raise PermissionDenied('Vous ne pouvez réserver qu’au nom de votre compte client.')
        try:
            client = Client.objects.get(user=self.request.user)
        except Client.DoesNotExist as error:
            raise PermissionDenied('Votre compte ne possède pas de profil client.') from error
        serializer.save(client=client, statut=Reservation.STATUS_PENDING)

    def perform_update(self, serializer):
        reservation = self.get_object()
        if is_staff_user(self.request.user) and any(
            field in serializer.validated_data
            and serializer.validated_data[field] != getattr(reservation, field)
            for field in ('date_debut', 'date_fin', 'espace', 'nombre_invites')
        ):
            raise PermissionDenied(
                'L’équipe ne peut pas modifier l’espace, les dates, les heures '
                'ni le nombre d’invités choisis par le client.'
            )
        requested_type = serializer.validated_data.get('type_evenement')
        if (
            is_staff_user(self.request.user)
            and requested_type is not None
            and requested_type.pk != reservation.type_evenement_id
        ):
            raise PermissionDenied('L’administrateur ne peut pas modifier le type d’événement choisi par le client.')
        if not is_staff_user(self.request.user) and (
            reservation.client.user_id != self.request.user.id
            or reservation.statut != Reservation.STATUS_PENDING
        ):
            raise PermissionDenied('Seule une réservation en attente vous appartenant peut être modifiée.')
        if not is_staff_user(self.request.user) and serializer.validated_data.get('statut', reservation.statut) != reservation.statut:
            raise PermissionDenied('Utilisez le bouton d’annulation pour changer le statut.')
        serializer.save()

    def perform_destroy(self, instance):
        if is_staff_user(self.request.user):
            with transaction.atomic():
                instance.paiements.all().delete()
                instance.delete()
            return
        if (
            instance.client.user_id != self.request.user.id
            or instance.statut != Reservation.STATUS_PENDING
        ):
            raise PermissionDenied('Seule une réservation en attente vous appartenant peut être supprimée.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if not is_staff_user(request.user) and reservation.client.user_id != request.user.id:
            raise PermissionDenied('Vous ne pouvez annuler que votre propre réservation.')
        if reservation.statut not in [Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED]:
            raise PermissionDenied('Cette réservation ne peut plus être annulée.')
        reservation.statut = Reservation.STATUS_CANCELLED
        reservation.save()
        return Response(ReservationSerializer(reservation).data)


class PaiementViewSet(viewsets.ModelViewSet):
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        paiements = Paiement.objects.select_related('reservation__client', 'reservation__espace', 'reservation__type_evenement')
        if is_staff_user(self.request.user):
            queryset = paiements.filter(envoye_admin=True)
        else:
            queryset = paiements.filter(reservation__client__user=self.request.user)
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.annotate(
                search_date=Cast('date_paiement', output_field=CharField()),
                search_amount=Cast('montant', output_field=CharField()),
            ).filter(
                Q(reference__icontains=query)
                | Q(reservation__client__nom__icontains=query)
                | Q(reservation__espace__nom__icontains=query)
                | Q(reservation__type_evenement__nom__icontains=query)
                | Q(statut__icontains=query)
                | Q(mode_paiement__icontains=query)
                | Q(search_date__icontains=query)
                | Q(search_amount__icontains=query)
            )
        return queryset

    def perform_create(self, serializer):
        if is_staff_user(self.request.user):
            serializer.save(envoye_admin=True)
            return
        if 'statut' in self.request.data:
            raise PermissionDenied('Seule l’équipe événementielle peut choisir le statut du paiement.')
        reservation = serializer.validated_data['reservation']
        if reservation.client.user_id != self.request.user.id:
            raise PermissionDenied('Vous ne pouvez créer un paiement que pour votre réservation.')
        serializer.save(envoye_admin=False)

    def perform_update(self, serializer):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut modifier les paiements.')
        if set(self.request.data.keys()) - {'reference', 'statut'}:
            raise PermissionDenied('L’équipe peut uniquement modifier le statut ou la référence du paiement.')
        serializer.save()

    def perform_destroy(self, instance):
        if not is_staff_user(self.request.user):
            raise PermissionDenied('Seule l’équipe événementielle peut supprimer les paiements.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        if is_staff_user(request.user):
            raise PermissionDenied('Seul le client peut envoyer son paiement à l’équipe.')
        paiement = self.get_object()
        if paiement.reservation.client.user_id != request.user.id:
            raise PermissionDenied('Vous ne pouvez envoyer que votre propre paiement.')
        if paiement.envoye_admin:
            raise ValidationError('Ce paiement a déjà été envoyé à l’équipe.')
        if paiement.statut == Paiement.STATUS_CANCELLED:
            raise ValidationError('Un paiement annulé ne peut pas être envoyé.')
        paiement.envoye_admin = True
        paiement.save(update_fields=['envoye_admin'])
        return Response(self.get_serializer(paiement).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        if is_staff_user(request.user):
            raise PermissionDenied('Seul le client peut annuler son paiement.')
        paiement = self.get_object()
        if paiement.reservation.client.user_id != request.user.id:
            raise PermissionDenied('Vous ne pouvez annuler que votre propre paiement.')
        if paiement.reservation.statut != Reservation.STATUS_PENDING:
            raise PermissionDenied('Le paiement ne peut être annulé que si la réservation est en attente.')
        if paiement.statut == Paiement.STATUS_CANCELLED:
            raise ValidationError('Ce paiement est déjà annulé.')
        paiement.statut = Paiement.STATUS_CANCELLED
        paiement.save()
        return Response(self.get_serializer(paiement).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_view(request):
    reservations = Reservation.objects.all()
    paiements = Paiement.objects.all()
    if not is_staff_user(request.user):
        reservations = reservations.filter(client__user=request.user)
        paiements = paiements.filter(reservation__client__user=request.user)
    return Response({
        'total_clients': Client.objects.count() if is_staff_user(request.user) else Client.objects.filter(user=request.user).count(),
        'total_espaces': Espace.objects.count(),
        'espaces_disponibles': Espace.objects.filter(disponible=True).count(),
        'total_types_evenements': TypeEvenement.objects.count(),
        'total_reservations': reservations.count(),
        'reservations_en_attente': reservations.filter(statut=Reservation.STATUS_PENDING).count(),
        'reservations_confirmees': reservations.filter(statut=Reservation.STATUS_CONFIRMED).count(),
        'paiements_recus': paiements.filter(statut=Paiement.STATUS_PAID).count(),
    })
