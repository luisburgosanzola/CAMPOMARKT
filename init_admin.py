from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username="tigre1234").exists():
    User.objects.create_superuser(
        username="tigre1234",
        email="tigre@gmail.com",
        password="Tigre0250."
    )
    print("ADMIN CREADO")