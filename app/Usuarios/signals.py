from allauth.account.signals import user_logged_in
from django.dispatch import receiver
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework_simplejwt.tokens import RefreshToken

@receiver(user_logged_in)
def on_google_login(request, user, **kwargs):
    """
    Cuando Google inicia sesión: emitimos tokens y redirigimos.
    """
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    # Respuesta con cookies igual que tu login normal
    resp = redirect('main_page')
    resp.set_cookie('access', access, max_age=60*60, httponly=True, samesite='Lax')
    resp.set_cookie('refresh', str(refresh), max_age=60*60*24*7, httponly=True, samesite='Lax')

    messages.success(request, f"Bienvenido, {user.first_name or user.username}")
    return resp
