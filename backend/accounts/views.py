from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.middleware.csrf import get_token
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_view(request):
    get_token(request)
    return Response({'detail': 'CSRF cookie set.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    login(request, user)
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    login(request, user)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = User.objects.filter(
        email__iexact=serializer.validated_data['email'],
        is_active=True,
    ).first()

    if user and user.email:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f'{settings.FRONTEND_URL}/?uid={uid}&token={token}'
        send_mail(
            'Réinitialisation de votre mot de passe',
            f'Pour choisir un nouveau mot de passe, ouvrez ce lien : {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

    return Response({
        'detail': 'Si cette adresse est associée à un compte, un lien de réinitialisation a été envoyé.',
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    user.set_password(serializer.validated_data['new_password'])
    user.save(update_fields=['password'])
    return Response({'detail': 'Votre mot de passe a été réinitialisé.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'detail': 'Déconnexion réussie.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not request.user.check_password(serializer.validated_data['old_password']):
        return Response({'detail': 'Mot de passe actuel incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    return Response({'detail': 'Mot de passe changé avec succès.'})


class UserListCreateView(ListCreateAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.method == 'POST' and request.user.role != User.ROLE_ADMIN and not request.user.is_superuser:
            raise PermissionDenied('Seuls les administrateurs peuvent créer des utilisateurs.')

    def perform_create(self, serializer):
        if (
            serializer.validated_data.get('role') == User.ROLE_ADMIN
            and not self.request.user.is_superuser
        ):
            raise PermissionDenied('Seul un superutilisateur peut créer un administrateur.')
        if serializer.validated_data.get('role') == User.ROLE_PARTICIPANT:
            raise PermissionDenied(
                'Les clients créent leur compte eux-mêmes avant de réserver un espace.'
            )
        serializer.save()

    def get_queryset(self):
        if self.request.user.role == User.ROLE_ADMIN or self.request.user.is_superuser:
            users = User.objects.all()
        else:
            users = User.objects.filter(id=self.request.user.id)
        query = self.request.query_params.get('q')
        if query:
            users = users.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(role__icontains=query)
            )
        return users.order_by('id')


class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == User.ROLE_ADMIN or self.request.user.is_superuser:
            return User.objects.all().order_by('id')
        return User.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        user = serializer.instance
        if (
            (self.request.user.role == User.ROLE_ADMIN or self.request.user.is_superuser)
            and user.role != User.ROLE_PARTICIPANT
            and serializer.validated_data.get('role') == User.ROLE_PARTICIPANT
        ):
            raise PermissionDenied(
                'Les clients créent leur compte eux-mêmes avant de réserver un espace.'
            )
        if (
            (self.request.user.role == User.ROLE_ADMIN or self.request.user.is_superuser)
            and user.role == User.ROLE_PARTICIPANT
        ):
            personal_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password')
            changed_fields = [
                field for field in personal_fields
                if field in serializer.validated_data
                and (
                    field == 'password'
                    or serializer.validated_data[field] != getattr(user, field)
                )
            ]
            if changed_fields:
                raise PermissionDenied('Un administrateur ne peut pas modifier les informations personnelles d’un client.')
        if (
            self.request.user.role != User.ROLE_ADMIN
            and not self.request.user.is_superuser
            and serializer.validated_data.get('role', self.request.user.role) != self.request.user.role
        ):
            raise PermissionDenied('Vous ne pouvez pas modifier votre rôle.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise PermissionDenied('Vous ne pouvez pas supprimer votre propre compte depuis cette page.')
        instance.delete()
