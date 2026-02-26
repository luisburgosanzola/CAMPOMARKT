def notificaciones_header(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False).count()
        last = request.user.notifications.all()[:5]
        return {"notif_unread": unread, "notif_last": last}
    return {"notif_unread": 0, "notif_last": []}
