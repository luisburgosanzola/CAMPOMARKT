from django.urls import path
from . import views

urlpatterns = [
    path("<int:notif_id>/", views.abrir_notificacion, name="abrir_notificacion"),
]
