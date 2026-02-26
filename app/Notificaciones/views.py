from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from app.Notificaciones.models import Notification

@login_required(login_url="login_page")
def abrir_notificacion(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save(update_fields=["is_read"])

    # ✅ lo lleva al detalle del producto publicado
    return redirect("detalle_producto", producto_id=notif.product.id)
