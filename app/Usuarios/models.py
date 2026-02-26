from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
import random
from datetime import timedelta


# =====================================================
# 👤 USUARIO PERSONALIZADO
# =====================================================
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLES = [
        ('cliente', 'Cliente'),
        ('productor', 'Productor'),
    ]

    rol = models.CharField(max_length=20, choices=ROLES, null=True, blank=True)

    profile_image = models.ImageField(
        upload_to="perfiles/",
        default="perfiles/default.png",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} ({self.rol or 'sin rol'})"


# =====================================================
# 🛒 PERFIL CLIENTE
# =====================================================
class Cliente(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cliente"
    )
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    telefono_verificado = models.BooleanField(default=False)

    def __str__(self):
        return f"Cliente: {self.usuario.username}"


# =====================================================
# 🌾 PERFIL PRODUCTOR
# =====================================================
class Productor(models.Model):

    CATEGORIAS = [
        ('frutas', 'Frutas'),
        ('verduras', 'Verduras'),
        ('tuberculos', 'Tubérculos'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="productor"
    )

    telefono = models.CharField(max_length=15, blank=True)
    nombre_finca = models.CharField(max_length=200, blank=True)

    # Guardamos múltiples categorías separadas por coma
    categorias_cultivo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ej: frutas,verduras"
    )

    def categorias_lista(self):
        """
        Devuelve las categorías como lista limpia
        """
        if not self.categorias_cultivo:
            return []
        return [c.strip() for c in self.categorias_cultivo.split(",")]

    def __str__(self):
        return f"Productor: {self.usuario.username}"


# =====================================================
# 📲 CÓDIGOS SMS DE VERIFICACIÓN
# =====================================================
class CodigoSMS(models.Model):
    telefono = models.CharField(max_length=20, unique=True)
    codigo = models.CharField(max_length=6)
    creado = models.DateTimeField(auto_now_add=True)

    def generar_codigo(self):
        self.codigo = str(random.randint(100000, 999999))
        self.creado = timezone.now()
        self.save()

    def esta_vencido(self):
        return timezone.now() > self.creado + timedelta(minutes=5)

    def __str__(self):
        return f"Código para {self.telefono}: {self.codigo}"


# =====================================================
# 📧 CÓDIGOS EMAIL DE VERIFICACIÓN
# =====================================================
class CodigoEmail(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="codigos_email"
    )
    email = models.EmailField()
    codigo = models.CharField(max_length=6)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    def esta_vencido(self):
        return timezone.now() > self.creado + timedelta(minutes=10)

    @staticmethod
    def generar():
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f"Código Email {self.email}"
