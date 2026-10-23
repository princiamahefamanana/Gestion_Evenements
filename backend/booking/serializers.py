from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Client, Espace, Paiement, Reservation, TypeEvenement


class ClientSerializer(serializers.ModelSerializer):
    telephone = serializers.RegexField(
        r'^\d{10}$',
        required=True,
        error_messages={'invalid': 'Le téléphone doit contenir exactement 10 chiffres.'},
    )

    class Meta:
        model = Client
        fields = ['id', 'nom', 'email', 'telephone', 'user', 'cree_le']
        read_only_fields = ['id', 'user', 'cree_le']

    @transaction.atomic
    def update(self, instance, validated_data):
        client = super().update(instance, validated_data)
        if client.user_id:
            client.user.phone = client.telephone
            client.user.save(update_fields=['phone'])
        return client

    def validate(self, attrs):
        telephone = attrs.get('telephone', self.instance.telephone if self.instance else '')
        if len(telephone) != 10 or not telephone.isdigit():
            raise serializers.ValidationError({
                'telephone': 'Le téléphone doit contenir exactement 10 chiffres.',
            })
        return attrs


class EspaceSerializer(serializers.ModelSerializer):
    tarif_horaire = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Espace.MIN_HOURLY_RATE,
        min_value=Espace.MIN_HOURLY_RATE,
    )

    class Meta:
        model = Espace
        fields = ['id', 'nom', 'adresse', 'capacite', 'tarif_horaire', 'description', 'disponible']

    def validate(self, attrs):
        rate = attrs.get('tarif_horaire')
        if rate is None and not self.instance:
            rate = Espace.MIN_HOURLY_RATE
            attrs['tarif_horaire'] = rate
        if rate is not None and rate < Espace.MIN_HOURLY_RATE:
            raise serializers.ValidationError({
                'tarif_horaire': 'Le tarif horaire minimum est de 100 000 Ar.',
            })
        return attrs


class TypeEvenementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeEvenement
        fields = ['id', 'nom', 'description']


class ReservationSerializer(serializers.ModelSerializer):
    nombre_invites = serializers.IntegerField(min_value=10)
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    espace_nom = serializers.CharField(source='espace.nom', read_only=True)
    type_evenement_nom = serializers.CharField(source='type_evenement.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'client', 'client_nom', 'espace', 'espace_nom',
            'type_evenement', 'type_evenement_nom', 'date_debut', 'date_fin',
            'nombre_invites', 'statut', 'statut_display', 'montant_total', 'cree_le',
        ]
        read_only_fields = ['id', 'montant_total', 'cree_le']
        extra_kwargs = {'client': {'required': False}}

    def validate(self, attrs):
        instance = self.instance or Reservation()
        espace = attrs.get('espace', instance.espace if instance.pk else None)
        client = attrs.get('client', instance.client if instance.pk else None)
        if client is None and not instance.pk:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                try:
                    client = request.user.client_profile
                except Client.DoesNotExist:
                    client = None
        date_debut = attrs.get('date_debut', instance.date_debut if instance.pk else None)
        date_fin = attrs.get('date_fin', instance.date_fin if instance.pk else None)
        nombre_invites = attrs.get('nombre_invites', instance.nombre_invites if instance.pk else None)
        statut = attrs.get('statut', instance.statut if instance.pk else Reservation.STATUS_PENDING)
        tarif_horaire = espace.tarif_horaire if espace else 0
        errors = {}
        if date_debut and date_fin and date_fin <= date_debut:
            errors['date_fin'] = 'La date de fin doit être postérieure à la date de début.'
        if nombre_invites is not None and nombre_invites < 10:
            errors['nombre_invites'] = 'Le nombre minimum d’invités est de 10.'
        if espace and nombre_invites and nombre_invites > espace.capacite:
            errors['nombre_invites'] = 'Le nombre d’invités dépasse la capacité de l’espace.'
        if espace and not espace.disponible and statut != Reservation.STATUS_CANCELLED:
            errors['espace'] = 'Cet espace n’est pas disponible à la réservation.'
        if espace and date_debut and date_fin and date_fin > date_debut and statut != Reservation.STATUS_CANCELLED:
            overlaps = Reservation.objects.filter(
                espace=espace,
                statut__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED],
                date_debut__lt=date_fin,
                date_fin__gt=date_debut,
            )
            if instance.pk:
                overlaps = overlaps.exclude(pk=instance.pk)
            if overlaps.exists():
                errors['espace'] = 'Cet espace est déjà réservé sur cette période.'
        if client and date_debut and date_fin and statut in [Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED]:
            duplicate = Reservation.objects.filter(
                client=client,
                date_debut=date_debut,
                date_fin=date_fin,
                statut__in=[Reservation.STATUS_PENDING, Reservation.STATUS_CONFIRMED],
            )
            if instance.pk:
                duplicate = duplicate.exclude(pk=instance.pk)
            if duplicate.exists():
                errors['date_debut'] = 'Ce client possède déjà une réservation aux mêmes date et heures.'
        if errors:
            raise serializers.ValidationError(errors)
        if espace and date_debut and date_fin and date_fin > date_debut:
            duration = Decimal(str((date_fin - date_debut).total_seconds())) / Decimal('3600')
            attrs['montant_total'] = (duration * tarif_horaire).quantize(Decimal('0.01'))
        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except ValidationError as error:
            raise serializers.ValidationError(error.message_dict if hasattr(error, 'message_dict') else error.messages) from error

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except ValidationError as error:
            raise serializers.ValidationError(error.message_dict if hasattr(error, 'message_dict') else error.messages) from error


class PaiementSerializer(serializers.ModelSerializer):
    montant = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    reservation_resume = serializers.SerializerMethodField()
    reservation_statut = serializers.CharField(source='reservation.statut', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = Paiement
        fields = [
            'id', 'reservation', 'reservation_resume', 'reservation_statut', 'montant',
            'mode_paiement', 'statut', 'statut_display', 'reference', 'envoye_admin', 'date_paiement',
        ]
        read_only_fields = ['id', 'date_paiement', 'envoye_admin']

    def validate_reservation(self, reservation):
        if reservation.montant_total <= 0:
            raise serializers.ValidationError(
                'Le montant de cette réservation n’a pas encore été calculé.'
            )
        return reservation

    def validate_reference(self, reference):
        reference = reference.strip()
        if reference:
            matching_payments = Paiement.objects.filter(reference__iexact=reference)
            if self.instance:
                matching_payments = matching_payments.exclude(pk=self.instance.pk)
            if matching_payments.exists():
                raise serializers.ValidationError('Cette référence de paiement est déjà utilisée.')
        return reference

    def validate(self, attrs):
        request = self.context.get('request')
        if request and not (
            request.user.is_superuser or request.user.role in ['admin', 'organizer']
        ) and self.initial_data.get('reference'):
            raise serializers.ValidationError({
                'reference': 'Seule l’équipe événementielle peut ajouter une référence.'
            })
        return attrs

    def create(self, validated_data):
        validated_data['montant'] = validated_data['reservation'].montant_total
        return super().create(validated_data)

    def get_reservation_resume(self, obj):
        return f'{obj.reservation.type_evenement.nom} — {obj.reservation.espace.nom}'
