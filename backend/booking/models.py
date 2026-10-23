from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator

MIN_SPACE_CAPACITY = 80
MIN_SPACE_HOURLY_RATE = Decimal('100000.00')


class Client(models.Model):
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_profile',
    )
    nom = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    telephone = models.CharField(
        max_length=30,
        blank=True,
        default='',
        validators=[RegexValidator(r'^\d{10}$', 'Le téléphone doit contenir exactement 10 chiffres.')],
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clients'
        ordering = ['nom', 'id']

    def __str__(self):
        return self.nom


class Espace(models.Model):
    MIN_CAPACITY = MIN_SPACE_CAPACITY
    MIN_HOURLY_RATE = MIN_SPACE_HOURLY_RATE

    nom = models.CharField(max_length=200)
    adresse = models.CharField(max_length=255)
    capacite = models.PositiveIntegerField(validators=[MinValueValidator(MIN_CAPACITY)])
    tarif_horaire = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=MIN_HOURLY_RATE,
        validators=[MinValueValidator(MIN_HOURLY_RATE)],
    )
    description = models.TextField(blank=True, default='')
    disponible = models.BooleanField(default=True)

    class Meta:
        db_table = 'espaces'
        ordering = ['nom', 'id']
        constraints = [
            models.CheckConstraint(
                check=models.Q(capacite__gte=MIN_SPACE_CAPACITY),
                name='espace_capacite_min_80',
            ),
            models.CheckConstraint(
                check=models.Q(tarif_horaire__gte=MIN_SPACE_HOURLY_RATE),
                name='espace_tarif_min_100000',
            ),
        ]

    def clean(self):
        errors = {}
        if self.capacite is not None and self.capacite < self.MIN_CAPACITY:
            errors['capacite'] = f'La capacité minimale d’un espace est de {self.MIN_CAPACITY} personnes.'
        if self.tarif_horaire is not None and self.tarif_horaire < self.MIN_HOURLY_RATE:
            errors['tarif_horaire'] = 'Le tarif horaire minimum est de 100 000 Ar.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class TypeEvenement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'types_evenements'
        ordering = ['nom', 'id']
        verbose_name = 'type d’événement'
        verbose_name_plural = 'types d’événements'

    def __str__(self):
        return self.nom


class Reservation(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_CONFIRMED, 'Confirmée'),
        (STATUS_CANCELLED, 'Annulée'),
        (STATUS_COMPLETED, 'Terminée'),
    ]

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='reservations')
    espace = models.ForeignKey(Espace, on_delete=models.PROTECT, related_name='reservations')
    type_evenement = models.ForeignKey(
        TypeEvenement,
        on_delete=models.PROTECT,
        related_name='reservations',
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    nombre_invites = models.PositiveIntegerField(validators=[MinValueValidator(10)])
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservations'
        ordering = ['-date_debut', '-id']

    def clean(self):
        errors = {}
        if self.date_debut and self.date_fin and self.date_fin <= self.date_debut:
            errors['date_fin'] = 'La date de fin doit être postérieure à la date de début.'
        if self.nombre_invites is not None and self.nombre_invites < 10:
            errors['nombre_invites'] = 'Le nombre minimum d’invités est de 10.'
        if self.espace_id and self.nombre_invites and self.nombre_invites > self.espace.capacite:
            errors['nombre_invites'] = 'Le nombre d’invités dépasse la capacité de l’espace.'
        if self.espace_id and not self.espace.disponible and self.statut != self.STATUS_CANCELLED:
            errors['espace'] = 'Cet espace n’est pas disponible à la réservation.'
        if self.espace_id and self.date_debut and self.date_fin and self.statut != self.STATUS_CANCELLED:
            overlaps = Reservation.objects.filter(
                espace_id=self.espace_id,
                statut__in=[self.STATUS_PENDING, self.STATUS_CONFIRMED],
                date_debut__lt=self.date_fin,
                date_fin__gt=self.date_debut,
            ).exclude(pk=self.pk)
            if overlaps.exists():
                errors['espace'] = 'Cet espace est déjà réservé sur cette période.'
        if (
            self.client_id
            and self.date_debut
            and self.date_fin
            and self.statut in [self.STATUS_PENDING, self.STATUS_CONFIRMED]
            and Reservation.objects.filter(
                client_id=self.client_id,
                date_debut=self.date_debut,
                date_fin=self.date_fin,
                statut__in=[self.STATUS_PENDING, self.STATUS_CONFIRMED],
            ).exclude(pk=self.pk).exists()
        ):
            errors['date_debut'] = 'Ce client possède déjà une réservation aux mêmes date et heures.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.type_evenement} — {self.espace} ({self.date_debut:%d/%m/%Y})'


class Paiement(models.Model):
    METHOD_CASH = 'cash'
    METHOD_TRANSFER = 'transfer'
    METHOD_CARD = 'card'
    METHOD_CHOICES = [
        (METHOD_CASH, 'Espèces'),
        (METHOD_TRANSFER, 'Virement'),
        (METHOD_CARD, 'Carte bancaire'),
    ]
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_PAID, 'Payé'),
        (STATUS_CANCELLED, 'Annulé'),
    ]

    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name='paiements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_CASH)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reference = models.CharField(max_length=100, blank=True, default='')
    envoye_admin = models.BooleanField(default=False)
    date_paiement = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'paiements'
        ordering = ['-date_paiement', '-id']

    def clean(self):
        if self.reference:
            matching_payments = Paiement.objects.filter(reference__iexact=self.reference.strip())
            if self.pk:
                matching_payments = matching_payments.exclude(pk=self.pk)
            if matching_payments.exists():
                raise ValidationError({
                    'reference': 'Cette référence de paiement est déjà utilisée.',
                })
        if self.montant is not None and self.montant <= 0:
            raise ValidationError({'montant': 'Le montant doit être supérieur à zéro.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.montant} — {self.reservation}'
