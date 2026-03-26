from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Guardar avatar de Google si está disponible
        extra = sociallogin.account.extra_data
        google_picture = extra.get("picture") or extra.get("avatar_url")

        # Si ya está vinculado => actualizar avatar si no tiene foto propia
        if sociallogin.is_existing:
            user = sociallogin.user
            if google_picture and not user.google_avatar:
                user.google_avatar = google_picture
                user.save(update_fields=["google_avatar"])
            return

        # Normalizar email
        email = (sociallogin.user.email or "").strip().lower()
        sociallogin.user.email = email

        # Guardar avatar en el objeto user antes de que allauth lo guarde
        if google_picture:
            sociallogin.user.google_avatar = google_picture

        # Si ya existe un usuario local con ese email -> vincular y entrar
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                if google_picture and not user.google_avatar:
                    user.google_avatar = google_picture
                    user.save(update_fields=["google_avatar"])
                sociallogin.connect(request, user)

    def is_open_for_signup(self, request, sociallogin):
        # Siempre permitir registro/login via Google
        return True
