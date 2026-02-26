"""
URL configuration for CampoMarkt project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from app.Productos import views as productos_views


from app.Productos.views import nosotros
#FOTO DE PERFIL
from django.conf import settings
from django.conf.urls.static import static




def main(request):
    return render(request, 'main.html')

def seguridad_aw(request):
    return render(request, 'seguridad_aw.html')


urlpatterns = [
    path('buscar/', productos_views.buscar_global, name='buscar_global'),

    path('admin/', admin.site.urls),

 
    path('', main, name='main'),

    path('chatbot/', include('Ashly.Ashly.chatbot.urls')),

    path('', include("app.Usuarios.urls")),
    path('producto/', include("app.Productos.urls")),

    path('nosotros/', nosotros, name='nosotros'),
    path('seguridad_aw/', seguridad_aw, name='seguridad_aw'),

    # ⭐ allauth (OBLIGATORIO)
    path('accounts/', include('allauth.urls')),
    path("notificaciones/", include("app.Notificaciones.urls")),


    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#FOTO DE PERFIL

