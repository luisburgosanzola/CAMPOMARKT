from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username="luis1234").exists():
    User.objects.create_superuser(
        username="luis1234",
        email="luis1234min@gmail.com",
        password="Tigre0250."
    )
    print("ADMIN CREADO")