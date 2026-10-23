from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.validators import RegexValidator


class EventSpaceUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields['role'] = self.model.ROLE_ADMIN
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_ORGANIZER = 'organizer'
    ROLE_PARTICIPANT = 'participant'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrateur'),
        (ROLE_ORGANIZER, 'Organisateur'),
        (ROLE_PARTICIPANT, 'Participant'),
    ]

    objects = EventSpaceUserManager()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PARTICIPANT)
    phone = models.CharField(
        max_length=30,
        blank=True,
        default='',
        validators=[RegexValidator(r'^\d{10}$', 'Le téléphone doit contenir exactement 10 chiffres.')],
    )

    class Meta:
        ordering = ['username']
        db_table = 'utilisateurs'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'
