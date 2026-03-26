from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

# Garantizar que el Site id=1 exista
Site.objects.update_or_create(
    id=1,
    defaults={
        'domain': 'awake-spirit-production-ebac.up.railway.app',
        'name': 'CampoMarkt',
    }
)

User = get_user_model()

if not User.objects.filter(username="tigre1234").exists():
    User.objects.create_superuser(
        username="tigre1234",
        email="tigre@gmail.com",
        password="Tigre0250."
    )
    print("ADMIN CREADO")