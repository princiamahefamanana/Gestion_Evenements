# Documentation API

## Authentification

- POST /api/auth/login/
- POST /api/auth/register/
- POST /api/auth/password-reset/
- POST /api/auth/password-reset/confirm/
- POST /api/auth/logout/
- GET /api/auth/me/
- POST /api/auth/change-password/

`password-reset/` accepte une adresse e-mail et renvoie toujours le même message,
qu'un compte existe ou non. En développement, le lien est imprimé dans la console
Django ; configurez SMTP dans `backend/.env` pour l'envoyer par e-mail.

## Espace événementiel

- GET, POST, PUT, PATCH, DELETE /api/clients/
- GET, POST, PUT, PATCH, DELETE /api/espaces/
- GET, POST, PUT, PATCH, DELETE /api/types-evenements/
- GET, POST, PUT, PATCH, DELETE /api/reservations/
- GET, POST, PUT, PATCH, DELETE /api/paiements/
- GET /api/tableau-de-bord/

Les réservations vérifient la capacité et la disponibilité de l’espace et refusent deux réservations qui se chevauchent. Le montant estimé est calculé avec le tarif
horaire fixe de 100 000 Ar de l’espace. Chaque espace doit avoir une capacité
d’au moins 80 personnes. Ces deux règles sont validées par l’API et par la base de données. Les comptes clients ne voient et ne réservent que leurs
propres réservations ; la gestion des espaces, des catégories et des paiements
est réservée à l’équipe événementielle.

Les administrateurs peuvent créer et modifier les espaces, dont le champ
`disponible`. Dans l’interface, « Désactiver » empêche les nouvelles réservations
de cette salle ; « Réactiver » la rend à nouveau sélectionnable par les clients.
