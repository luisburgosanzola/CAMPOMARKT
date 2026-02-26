from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def _get_process(self, request):
        return (
            (request.GET.get("process") or "")
            or (request.POST.get("process") or "")
            or (request.session.get("socialaccount_process") or "")
            or (request.session.get("process") or "")
        ).lower()

    def pre_social_login(self, request, sociallogin):
        # Si ya existe el socialaccount (Google ya linkeado) => login normal
        if sociallogin.is_existing:
            return

        process = self._get_process(request)

        # Normalizar email
        email = (sociallogin.user.email or "").strip().lower()
        sociallogin.user.email = email

        # Si ya existe usuario local con ese email -> link + login
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                sociallogin.connect(request, user)
                return

        # Si viene desde LOGIN y no existe usuario -> mandarlo a registrarse
        if process == "login":
            messages.error(request, "Ese correo no está registrado. Regístrate primero.")
            raise ImmediateHttpResponse(redirect("register_page"))

        # Si viene desde SIGNUP -> dejamos que allauth cree la cuenta
        return

    def is_open_for_signup(self, request, sociallogin):
        # Solo cerramos signup cuando vienen desde LOGIN
        process = self._get_process(request)
        return process != "login"
