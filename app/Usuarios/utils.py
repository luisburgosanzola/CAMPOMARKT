
from django.conf import settings
from django.core.mail import send_mail

def enviar_sms_verificacion(telefono, codigo):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    mensaje = f"Tu código de verificación CampoMarkt es: {codigo}"
    client.messages.create(
        body=mensaje,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=telefono
    )

def enviar_codigo_email(email, codigo):
    asunto = "Código de verificación - CampoMarkt"
    mensaje = f"Tu código de verificación es: {codigo}\n\nEste código vence en 10 minutos."
    send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)