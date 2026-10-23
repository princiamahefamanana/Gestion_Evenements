from django.urls import path
from .views import (
    UserDetailView,
    UserListCreateView,
    change_password_view,
    csrf_view,
    login_view,
    logout_view,
    me_view,
    password_reset_confirm_view,
    password_reset_request_view,
    register_view,
)

urlpatterns = [
    path('csrf/', csrf_view, name='csrf'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('password-reset/', password_reset_request_view, name='password-reset'),
    path('password-reset/confirm/', password_reset_confirm_view, name='password-reset-confirm'),
    path('logout/', logout_view, name='logout'),
    path('me/', me_view, name='me'),
    path('change-password/', change_password_view, name='change-password'),
    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
