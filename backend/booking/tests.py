from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Client, Espace, Paiement, Reservation, TypeEvenement


class ReservationApiTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username='gestionnaire',
            email='gestionnaire@example.com',
            password='Mot-de-passe-solide-42!',
            role=User.ROLE_ADMIN,
        )
        self.user = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='Mot-de-passe-solide-42!',
            role=User.ROLE_PARTICIPANT,
        )
        self.client_record = Client.objects.create(
            user=self.user,
            nom='Client Exemple',
            email=self.user.email,
        )
        self.other_client = Client.objects.create(
            nom='Autre Client',
            email='autre@example.com',
        )
        self.espace = Espace.objects.create(
            nom='Salle principale',
            adresse='1 rue des Événements',
            capacite=120,
            tarif_horaire=Decimal('100000.00'),
        )
        self.type_evenement, _ = TypeEvenement.objects.get_or_create(nom='Mariage')
        self.date_debut = timezone.now() + timedelta(days=3)
        self.date_fin = self.date_debut + timedelta(hours=4)

    def reservation_data(self, client=None, **overrides):
        data = {
            'client': client or self.client_record.pk,
            'espace': self.espace.pk,
            'type_evenement': self.type_evenement.pk,
            'date_debut': self.date_debut.isoformat(),
            'date_fin': self.date_fin.isoformat(),
            'nombre_invites': 80,
        }
        data.update(overrides)
        return data

    def test_staff_can_create_reservation_with_calculated_amount(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post('/api/reservations/', self.reservation_data(), format='json')

        self.assertEqual(response.status_code, 201, response.data)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.montant_total, Decimal('400000.00'))
        self.assertEqual(reservation.statut, Reservation.STATUS_PENDING)

    def test_staff_can_choose_reservation_start_and_end_times(self):
        self.client.force_authenticate(self.staff)
        start = self.date_debut.replace(hour=10, minute=30, second=0, microsecond=0)
        end = start + timedelta(hours=3, minutes=15)

        response = self.client.post(
            '/api/reservations/',
            self.reservation_data(date_debut=start.isoformat(), date_fin=end.isoformat()),
            format='json',
        )

        self.assertEqual(response.status_code, 201, response.data)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.date_debut, start)
        self.assertEqual(reservation.date_fin, end)
        self.assertEqual(reservation.montant_total, Decimal('325000.00'))

    def test_staff_cannot_change_client_reservation_event_type(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
        )
        other_type, _ = TypeEvenement.objects.get_or_create(nom='Conférence')
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            f'/api/reservations/{reservation.pk}/',
            {'type_evenement': other_type.pk},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        reservation.refresh_from_db()
        self.assertEqual(reservation.type_evenement, self.type_evenement)

    def test_staff_cannot_change_client_reservation_dates_or_times(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
        )
        other_space = Espace.objects.create(
            nom='Salle secondaire',
            adresse='2 rue des Événements',
            capacite=120,
        )
        self.client.force_authenticate(self.staff)

        for field, value in (
            ('date_debut', (self.date_debut - timedelta(hours=1)).isoformat()),
            ('date_fin', (self.date_fin + timedelta(hours=1)).isoformat()),
            ('espace', other_space.pk),
            ('nombre_invites', 90),
        ):
            with self.subTest(field=field):
                response = self.client.patch(
                    f'/api/reservations/{reservation.pk}/',
                    {field: value},
                    format='json',
                )

                self.assertEqual(response.status_code, 403)
                reservation.refresh_from_db()
                self.assertEqual(reservation.date_debut, self.date_debut)
                self.assertEqual(reservation.date_fin, self.date_fin)
                self.assertEqual(reservation.espace, self.espace)
                self.assertEqual(reservation.nombre_invites, 80)

        response = self.client.patch(
            f'/api/reservations/{reservation.pk}/',
            {'statut': Reservation.STATUS_CONFIRMED},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        reservation.refresh_from_db()
        self.assertEqual(reservation.statut, Reservation.STATUS_CONFIRMED)
        self.assertEqual(reservation.date_debut, self.date_debut)
        self.assertEqual(reservation.date_fin, self.date_fin)

    def test_overlapping_reservation_is_rejected(self):
        Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
        )
        self.client.force_authenticate(self.staff)

        response = self.client.post('/api/reservations/', self.reservation_data(), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('espace', response.data)

    def test_client_cannot_create_duplicate_reservation_for_same_date_and_hours(self):
        Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
        )
        other_space = Espace.objects.create(
            nom='Salle secondaire',
            adresse='2 rue des Événements',
            capacite=100,
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/reservations/',
            self.reservation_data(espace=other_space.pk),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('date_debut', response.data)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_capacity_is_validated(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            '/api/reservations/',
            self.reservation_data(nombre_invites=121),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('nombre_invites', response.data)

    def test_reservation_requires_at_least_ten_guests(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            '/api/reservations/',
            self.reservation_data(nombre_invites=9),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('nombre_invites', response.data)

    def test_reservation_model_rejects_fewer_than_ten_guests(self):
        reservation = Reservation(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=9,
        )

        with self.assertRaises(ValidationError):
            reservation.save()

    def test_payment_amount_is_calculated_from_reservation_duration_and_hourly_rate(self):
        self.client.force_authenticate(self.staff)
        start = self.date_debut
        end = start + timedelta(hours=3)
        reservation_response = self.client.post(
            '/api/reservations/',
            self.reservation_data(
                date_debut=start.isoformat(),
                date_fin=end.isoformat(),
            ),
            format='json',
        )
        self.assertEqual(reservation_response.status_code, 201, reservation_response.data)

        payment_response = self.client.post(
            '/api/paiements/',
            {
                'reservation': reservation_response.data['id'],
                'montant': '1.00',
                'mode_paiement': 'cash',
                'statut': 'pending',
            },
            format='json',
        )

        self.assertEqual(payment_response.status_code, 201, payment_response.data)
        self.assertEqual(Decimal(payment_response.data['montant']), Decimal('300000.00'))
        self.assertEqual(Paiement.objects.get().montant, Decimal('300000.00'))

    def test_client_can_create_payment_with_calculated_amount_and_default_pending_status(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_debut + timedelta(hours=3),
            nombre_invites=80,
            montant_total=Decimal('300000.00'),
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/paiements/',
            {
                'reservation': reservation.pk,
                'montant': '1.00',
                'mode_paiement': 'transfer',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Decimal(response.data['montant']), Decimal('300000.00'))
        self.assertEqual(response.data['statut'], Paiement.STATUS_PENDING)
        self.assertFalse(response.data['envoye_admin'])

    def test_client_cannot_choose_payment_status(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_debut + timedelta(hours=3),
            nombre_invites=80,
            montant_total=Decimal('300000.00'),
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/paiements/',
            {'reservation': reservation.pk, 'statut': 'paid'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Paiement.objects.count(), 0)

    def test_client_cannot_add_payment_reference_or_pay_for_another_client(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_debut + timedelta(hours=3),
            nombre_invites=80,
            montant_total=Decimal('300000.00'),
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/paiements/',
            {
                'reservation': reservation.pk,
                'reference': 'CLIENT-REF',
                'statut': 'pending',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('reference', response.data)
        self.assertEqual(Paiement.objects.count(), 0)

        reservation.client = self.other_client
        reservation.save()
        response = self.client.post(
            '/api/paiements/',
            {'reservation': reservation.pk, 'statut': 'pending'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_change_payment_status_and_reference_but_not_amount(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_debut + timedelta(hours=3),
            nombre_invites=80,
            montant_total=Decimal('300000.00'),
        )
        paiement = Paiement.objects.create(
            reservation=reservation,
            montant=Decimal('300000.00'),
            statut=Paiement.STATUS_PENDING,
        )
        self.client.force_authenticate(self.staff)

        response = self.client.get('/api/paiements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        self.client.force_authenticate(self.user)
        response = self.client.post(f'/api/paiements/{paiement.pk}/send/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['envoye_admin'])

        self.client.force_authenticate(self.staff)
        response = self.client.get('/api/paiements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        response = self.client.patch(
            f'/api/paiements/{paiement.pk}/',
            {'reference': 'ADMIN-REF-001', 'statut': 'paid', 'montant': '1.00'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.patch(
            f'/api/paiements/{paiement.pk}/',
            {'reference': 'ADMIN-REF-001', 'statut': 'paid'},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['reference'], 'ADMIN-REF-001')
        self.assertEqual(Decimal(response.data['montant']), Decimal('300000.00'))
        self.assertEqual(response.data['statut'], Paiement.STATUS_PAID)

    def test_client_can_cancel_payment_only_while_reservation_is_pending(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_debut + timedelta(hours=3),
            nombre_invites=80,
            montant_total=Decimal('300000.00'),
        )
        paiement = Paiement.objects.create(
            reservation=reservation,
            montant=Decimal('300000.00'),
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(f'/api/paiements/{paiement.pk}/send/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.data)

        response = self.client.post(f'/api/paiements/{paiement.pk}/cancel/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['statut'], Paiement.STATUS_CANCELLED)

        paiement.statut = Paiement.STATUS_PENDING
        paiement.save()
        reservation.statut = Reservation.STATUS_CONFIRMED
        reservation.save()
        response = self.client.post(f'/api/paiements/{paiement.pk}/cancel/', {}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_payment_reference_cannot_be_reused(self):
        self.client.force_authenticate(self.staff)
        first_reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
            montant_total=Decimal('400000.00'),
        )
        second_reservation = Reservation.objects.create(
            client=self.other_client,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut + timedelta(days=1),
            date_fin=self.date_fin + timedelta(days=1),
            nombre_invites=80,
            montant_total=Decimal('400000.00'),
        )
        first_response = self.client.post(
            '/api/paiements/',
            {
                'reservation': first_reservation.pk,
                'reference': 'REF-UNIQUE-001',
                'statut': 'pending',
            },
            format='json',
        )
        self.assertEqual(first_response.status_code, 201, first_response.data)

        duplicate_response = self.client.post(
            '/api/paiements/',
            {
                'reservation': second_reservation.pk,
                'reference': 'ref-unique-001',
                'statut': 'pending',
            },
            format='json',
        )

        self.assertEqual(duplicate_response.status_code, 400)
        self.assertIn('reference', duplicate_response.data)
        self.assertEqual(Paiement.objects.count(), 1)

    def test_client_cannot_reserve_for_another_client(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            '/api/reservations/',
            self.reservation_data(client=self.other_client.pk),
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_client_can_create_own_reservation_without_sending_client_id(self):
        self.client.force_authenticate(self.user)
        data = self.reservation_data()
        del data['client']

        response = self.client.post('/api/reservations/', data, format='json')

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Reservation.objects.get().client, self.client_record)

    def test_client_can_edit_and_delete_own_pending_reservation(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
        )
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f'/api/reservations/{reservation.pk}/',
            {'nombre_invites': 90},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        reservation.refresh_from_db()
        self.assertEqual(reservation.nombre_invites, 90)

        response = self.client.delete(f'/api/reservations/{reservation.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Reservation.objects.filter(pk=reservation.pk).exists())

    def test_staff_can_delete_confirmed_reservation_and_its_payments(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
            statut=Reservation.STATUS_CONFIRMED,
        )
        payment = Paiement.objects.create(
            reservation=reservation,
            montant=Decimal('400000.00'),
            reference='RESERVATION-A-SUPPRIMER',
        )
        self.client.force_authenticate(self.staff)

        response = self.client.delete(f'/api/reservations/{reservation.pk}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Reservation.objects.filter(pk=reservation.pk).exists())
        self.assertFalse(Paiement.objects.filter(pk=payment.pk).exists())

    def test_client_can_cancel_own_confirmed_reservation(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
            statut=Reservation.STATUS_CONFIRMED,
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(f'/api/reservations/{reservation.pk}/cancel/')

        self.assertEqual(response.status_code, 200, response.data)
        reservation.refresh_from_db()
        self.assertEqual(reservation.statut, Reservation.STATUS_CANCELLED)

    def test_client_cannot_edit_confirmed_reservation(self):
        reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
            statut=Reservation.STATUS_CONFIRMED,
        )
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f'/api/reservations/{reservation.pk}/',
            {'nombre_invites': 90},
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_can_search_spaces_by_name(self):
        self.client.force_authenticate(self.staff)

        response = self.client.get('/api/espaces/', {'q': 'principale'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [self.espace.pk])

    def test_staff_can_change_space_availability(self):
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            f'/api/espaces/{self.espace.pk}/',
            {'disponible': False},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.espace.refresh_from_db()
        self.assertFalse(self.espace.disponible)

    def test_space_creation_uses_minimum_rate_and_capacity(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            '/api/espaces/',
            {
                'nom': 'Nouvelle salle',
                'adresse': '3 rue des Événements',
                'capacite': 80,
                'description': '',
                'disponible': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Decimal(response.data['tarif_horaire']), Decimal('100000.00'))
        self.assertEqual(Espace.objects.get(nom='Nouvelle salle').capacite, 80)

    def test_staff_can_set_hourly_rate_above_minimum(self):
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            f'/api/espaces/{self.espace.pk}/',
            {'tarif_horaire': '125000.00'},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.espace.refresh_from_db()
        self.assertEqual(self.espace.tarif_horaire, Decimal('125000.00'))

    def test_staff_cannot_set_hourly_rate_below_minimum(self):
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            f'/api/espaces/{self.espace.pk}/',
            {'tarif_horaire': '99999.99'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('tarif_horaire', response.data)
        self.espace.refresh_from_db()
        self.assertEqual(self.espace.tarif_horaire, Espace.MIN_HOURLY_RATE)

    def test_space_capacity_below_eighty_is_rejected(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            '/api/espaces/',
            {
                'nom': 'Salle trop petite',
                'adresse': '4 rue des Événements',
                'capacite': 79,
                'disponible': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('capacite', response.data)

    def test_space_model_rejects_capacity_below_eighty(self):
        space = Espace(
            nom='Salle invalide',
            adresse='5 rue des Événements',
            capacite=79,
        )

        with self.assertRaises(ValidationError):
            space.save()

    def test_space_model_accepts_hourly_rate_above_minimum(self):
        self.espace.tarif_horaire = Decimal('125000.00')

        self.espace.save()
        self.espace.refresh_from_db()
        self.assertEqual(self.espace.tarif_horaire, Decimal('125000.00'))

    def test_space_model_rejects_hourly_rate_below_minimum(self):
        self.espace.tarif_horaire = Decimal('99999.99')

        with self.assertRaises(ValidationError):
            self.espace.save()

    def test_client_phone_must_contain_exactly_ten_digits(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            '/api/clients/',
            {'nom': 'Nouveau Client', 'email': 'nouveau@example.com', 'telephone': '123456789'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('telephone', response.data)

    def test_staff_cannot_create_client_without_a_reservation(self):
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            '/api/clients/',
            {'nom': 'Nouveau Client', 'email': 'nouveau@example.com', 'telephone': '0123456789'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Client.objects.count(), 2)

    def test_staff_cannot_edit_client_personal_information(self):
        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            f'/api/clients/{self.client_record.pk}/',
            {'telephone': '0123456789', 'nom': 'Nom modifié'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.client_record.refresh_from_db()
        self.assertEqual(self.client_record.telephone, '')
        self.assertEqual(self.client_record.nom, 'Client Exemple')

    def test_staff_can_delete_client(self):
        self.client.force_authenticate(self.staff)

        response = self.client.delete(f'/api/clients/{self.other_client.pk}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Client.objects.filter(pk=self.other_client.pk).exists())

    def test_staff_cannot_delete_client_with_reservations(self):
        Reservation.objects.create(
            client=self.other_client,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
        )
        self.client.force_authenticate(self.staff)

        response = self.client.delete(f'/api/clients/{self.other_client.pk}/')

        self.assertEqual(response.status_code, 400)
        self.assertIn('réservations', str(response.data).lower())
        self.assertTrue(Client.objects.filter(pk=self.other_client.pk).exists())

    def test_client_cannot_change_space_availability(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            f'/api/espaces/{self.espace.pk}/',
            {'disponible': False},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.espace.refresh_from_db()
        self.assertTrue(self.espace.disponible)

    def test_dashboard_reports_space_availability_for_staff(self):
        Espace.objects.create(
            nom='Salle indisponible',
            adresse='2 rue des Événements',
            capacite=80,
            disponible=False,
        )
        self.client.force_authenticate(self.staff)

        response = self.client.get('/api/tableau-de-bord/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_espaces'], 2)
        self.assertEqual(response.data['espaces_disponibles'], 1)

    def test_client_can_search_only_their_payments(self):
        own_reservation = Reservation.objects.create(
            client=self.client_record,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut,
            date_fin=self.date_fin,
            nombre_invites=80,
        )
        own_payment = Paiement.objects.create(
            reservation=own_reservation,
            montant=Decimal('50000.00'),
            reference='PAIEMENT-RECHERCHE',
        )
        other_reservation = Reservation.objects.create(
            client=self.other_client,
            espace=self.espace,
            type_evenement=self.type_evenement,
            date_debut=self.date_debut + timedelta(days=1),
            date_fin=self.date_fin + timedelta(days=1),
            nombre_invites=80,
        )
        Paiement.objects.create(
            reservation=other_reservation,
            montant=Decimal('50000.00'),
            reference='PAIEMENT-RECHERCHE-AUTRE',
        )
        self.client.force_authenticate(self.user)

        response = self.client.get('/api/paiements/', {'q': 'PAIEMENT-RECHERCHE'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [own_payment.pk])
