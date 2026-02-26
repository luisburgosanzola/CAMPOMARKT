from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterJWTView, ProfileAPIView, EnviarCodigoSMSView
from . import views_html

urlpatterns = [
    # API
    path('auth/register/', RegisterJWTView.as_view(), name='auth-register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', ProfileAPIView.as_view(), name='profile_api'),

    # SMS
    path("enviar-sms/", EnviarCodigoSMSView.as_view(), name="enviar_sms"),

    # Google
    path("google/completar/", views_html.google_completo, name="google_completo"),
    path("google/seleccionar-rol/", views_html.seleccionar_rol_google, name="seleccionar_rol_google"),

    # Perfiles
    path("cliente/completar/", views_html.completar_cliente, name="completar_cliente"),
    path("productor/completar/", views_html.completar_productor, name="completar_productor"),

    # HTML
    path('register/', views_html.register_page, name='register_page'),
    path('login/', views_html.login_page, name='login_page'),
    path('main/', views_html.main_page, name='main_page'),
    path('logout/', views_html.logout_page, name='logout_page'),
    path('profile/', views_html.profile_page, name='mi_perfil'),

    # ✅ AQUÍ
    path("verify-email/", views_html.verify_email, name="verify_email"),

    path("google/signup/", views_html.google_signup_start, name="google_signup_start"),
    path("productor/<str:username>/", views_html.perfil_productor_publico, name="perfil_productor_publico"),


]
