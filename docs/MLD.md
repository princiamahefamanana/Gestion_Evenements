# Modèle logique — Espace événementiel

- `utilisateurs` : comptes d’accès et rôles (modèle d’authentification Django).
- `clients` : nom, e-mail, téléphone et lien facultatif avec un compte.
- `espaces` : nom, adresse, capacité (80 personnes minimum), tarif fixe de 100 000 Ar par heure, description et disponibilité.
- `types_evenements` : catégories d’événements, par exemple mariage, anniversaire ou conférence.
- `reservations` : client, espace, type, période, nombre d’invités, statut et montant estimé.
- `paiements` : réservation, montant, mode, statut, référence et date.

