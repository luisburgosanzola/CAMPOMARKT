from django.db import models
from app.Usuarios.models import User


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):

    UNIDAD_MEDIDA = [
        ('kg', 'Kilogramos'),
        ('g', 'Gramos'),
        ('ton', 'Toneladas'),
        ('unidad', 'Unidad'),
        ('caja', 'Caja'),
        ('bulto', 'Bulto'),
    ]

    CALIDAD = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]

    ESTADO_PUBLICACION = [
        ('disponible', 'Disponible'),
        ('vendido', 'Vendido'),
        ('pausado', 'Pausado'),
    ]

    # 🔥 SOLO productores pueden crear productos
    productor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='productos',
        limit_choices_to={'rol': 'productor'},   # 👈 IMPORTANTE
    )

    # Datos básicos
    nombre = models.CharField(max_length=150)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    descripcion = models.TextField(blank=True, null=True)

    # Cantidad / precios
    unidad_medida = models.CharField(
        max_length=10,
        choices=UNIDAD_MEDIDA,
        default='kg'
    )
    cantidad_disponible = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    precio_unitario = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    calidad = models.CharField(
        max_length=10,
        choices=CALIDAD,
        default='media'
    )

    # 📍 Ubicación y contacto
    departamento = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    municipio = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    fecha_disponibilidad = models.DateField(
        blank=True,
        null=True
    )

    # Imágenes
    imagen_principal = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True
    )
    imagen_secundaria = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True
    )

    # Estado publicación
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_PUBLICACION,
        default='disponible'
    )

    # Favoritos
    favoritos = models.ManyToManyField(
        User,
        related_name='productos_favoritos',
        blank=True
    )

    def __str__(self):
        productor_nombre = self.productor.username if self.productor else "Sin productor"
        return f"{self.nombre} - {productor_nombre} ({self.estado})"


class Oferta(models.Model):
    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name="oferta"
    )

    productor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ofertas",
        limit_choices_to={'rol': 'productor'},
    )

    # Precio oferta (más simple que % por ahora)
    precio_oferta = models.CharField(max_length=50)

    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Oferta: {self.producto.nombre} - {self.precio_oferta}"
