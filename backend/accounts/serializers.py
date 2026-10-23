from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from booking.models import Client
from .models import User


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(min_length=3, max_length=150)
    first_name = serializers.CharField(min_length=3, max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(min_length=3, max_length=150, required=False, allow_blank=True)
    phone = serializers.RegexField(
        r'^\d{10}$',
        required=True,
        error_messages={'invalid': 'Le téléphone doit contenir exactement 10 chiffres.'},
    )
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'phone', 'is_superuser', 'password']
        read_only_fields = ['is_superuser']

    def validate(self, attrs):
        phone = attrs.get('phone', self.instance.phone if self.instance else '')
        if len(phone) != 10 or not phone.isdigit():
            raise serializers.ValidationError({
                'phone': 'Le téléphone doit contenir exactement 10 chiffres.',
            })
        email = attrs.get('email')
        if email:
            matching_users = User.objects.filter(email__iexact=email)
            matching_clients = Client.objects.filter(email__iexact=email)
            if self.instance:
                matching_users = matching_users.exclude(pk=self.instance.pk)
                matching_clients = matching_clients.exclude(user=self.instance)
            if matching_users.exists() or matching_clients.exists():
                raise serializers.ValidationError({'email': 'Cette adresse e-mail est déjà utilisée.'})
        if not self.instance and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Le mot de passe est obligatoire.'})
        if attrs.get('password'):
            try:
                validate_password(attrs['password'], user=self.instance)
            except ValidationError as error:
                raise serializers.ValidationError({'password': list(error.messages)}) from error
        return attrs

    def validate_username(self, value):
        if value.isdigit():
            raise serializers.ValidationError('Le nom d’utilisateur ne peut pas être composé uniquement de chiffres.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        if user.role == User.ROLE_PARTICIPANT and user.email:
            Client.objects.create(
                user=user,
                nom=user.get_full_name().strip() or user.username,
                email=user.email,
                telephone=user.phone,
            )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        if user.role == User.ROLE_PARTICIPANT and user.email:
            Client.objects.update_or_create(
                user=user,
                defaults={
                    'nom': user.get_full_name().strip() or user.username,
                    'email': user.email,
                    'telephone': user.phone,
                },
            )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Identifiants invalides.')
        if not user.is_active:
            raise serializers.ValidationError('Compte désactivé.')
        return {'user': user}


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    first_name = serializers.CharField(min_length=3, max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(min_length=3, max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        if value.isdigit():
            raise serializers.ValidationError('Le nom d’utilisateur ne peut pas être composé uniquement de chiffres.')
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Ce nom d’utilisateur est déjà utilisé.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Cette adresse e-mail est déjà utilisée.')
        if Client.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Cette adresse e-mail est déjà utilisée.')
        return value

    def validate(self, attrs):
        try:
            validate_password(attrs['password'])
        except ValidationError as error:
            raise serializers.ValidationError({'password': list(error.messages)}) from error
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            **validated_data,
            password=password,
            role=User.ROLE_PARTICIPANT,
        )
        Client.objects.create(user=user, nom=user.username, email=user.email)
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode

        try:
            user_id = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as error:
            raise serializers.ValidationError({'token': 'Lien de réinitialisation invalide ou expiré.'}) from error

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': 'Lien de réinitialisation invalide ou expiré.'})

        try:
            validate_password(attrs['new_password'], user=user)
        except ValidationError as error:
            raise serializers.ValidationError({'new_password': list(error.messages)}) from error

        attrs['user'] = user
        return attrs
