from django.db.models.signals import post_save
from django.dispatch import receiver
from app.Productos.models import Producto
from app.Usuarios.models import User
from app.Notificaciones.models import Notification

@receiver(post_save, sender=Producto)
def crear_notificacion_producto(sender, instance, created, **kwargs):
    if not created:
        return

    # ✅ Notificar SOLO a clientes
    clientes = User.objects.filter(rol="cliente")

    Notification.objects.bulk_create([
        Notification(
            user=c,
            product=instance,
            message=f"🆕 Nuevo producto: {instance.nombre}"
        )
        for c in clientes
    ])

from django.db.models.signals import post_save
from django.dispatch import receiver
from app.Productos.models import Oferta
from app.Usuarios.models import User
from app.Notificaciones.models import Notification

@receiver(post_save, sender=Oferta)
def notificar_oferta(sender, instance, created, **kwargs):
    # ✅ solo cuando se CREA la oferta (evita spam por edición)
    if not created:
        return

    clientes = User.objects.filter(rol="cliente")

    Notification.objects.bulk_create([
        Notification(
            user=c,
            product=instance.producto,
            message=f"🔥 Nueva oferta: {instance.producto.nombre}"
        )
        for c in clientes
    ])
