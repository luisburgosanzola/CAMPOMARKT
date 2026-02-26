from rest_framework import serializers
from django.db import transaction
from .models import User, Cliente, Productor


# ==========================
#   USER SERIALIZER
# ==========================

class UserSerializer(serializers.ModelSerializer):
    # Para que devuelva URL completa de la imagen si existe
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'rol',
            'profile_image'
        ]


# ==========================
#   SERIALIZERS DE PERFIL
# ==========================

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'direccion', 'telefono', 'telefono_verificado']


class ProductorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Productor
        fields = ['id', 'telefono', 'nombre_finca', 'categorias_cultivo']


# ==========================
#   REGISTER SERIALIZER
# ==========================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)

    # Cliente
    direccion = serializers.CharField(write_only=True, required=False, allow_blank=True)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Productor (compatibilidad: acepta telefono_productor O telefono)
    telefono_productor = serializers.CharField(write_only=True, required=False, allow_blank=True)
    nombre_finca = serializers.CharField(write_only=True, required=False, allow_blank=True)

    categorias_cultivo = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'rol',
            'password', 'password2',
            'direccion', 'telefono',
            'telefono_productor', 'nombre_finca', 'categorias_cultivo',
        ]

    def validate(self, attrs):
        errores = {}

        if attrs.get('password') != attrs.get('password2'):
            errores['password2'] = ["Las contraseñas no coinciden."]

        rol = attrs.get('rol')
        if rol not in ['cliente', 'productor']:
            errores['rol'] = ["Debes seleccionar un rol válido (cliente o productor)."]

        # ✅ CLIENTE
        if rol == 'cliente':
            if not (attrs.get('direccion') or '').strip():
                errores.setdefault('direccion', []).append("La dirección es obligatoria para clientes.")

            tel = (attrs.get('telefono') or '').strip()
            if not tel:
                errores.setdefault('telefono', []).append("El teléfono es obligatorio para clientes.")
            else:
                if not tel.isdigit():
                    errores.setdefault('telefono', []).append("El teléfono solo puede contener números.")
                if not 7 <= len(tel) <= 15:
                    errores.setdefault('telefono', []).append("El teléfono debe tener entre 7 y 15 dígitos.")

        # ✅ PRODUCTOR
        elif rol == 'productor':
            if not (attrs.get('nombre_finca') or '').strip():
                errores.setdefault('nombre_finca', []).append("El nombre de la finca es obligatorio para productores.")

            # 👇 acepta telefono_productor, pero si no viene usa telefono
            telp = (attrs.get('telefono_productor') or attrs.get('telefono') or '').strip()
            if not telp:
                errores.setdefault('telefono', []).append("El teléfono es obligatorio para productores.")
            else:
                if not telp.isdigit():
                    errores.setdefault('telefono', []).append("El teléfono solo puede contener números.")
                if not 7 <= len(telp) <= 15:
                    errores.setdefault('telefono', []).append("El teléfono debe tener entre 7 y 15 dígitos.")

            cats = attrs.get('categorias_cultivo') or []
            allowed = {"frutas", "verduras", "tuberculos"}
            cats = [c for c in cats if c in allowed]

            if not cats:
                errores.setdefault('categorias_cultivo', []).append(
                    "Selecciona al menos una categoría (frutas, verduras o tubérculos)."
                )

            # guardar
            attrs['categorias_cultivo'] = cats
            attrs['telefono_productor'] = telp  # normalizado

        if errores:
            raise serializers.ValidationError(errores)

        return attrs

    def create(self, validated_data):
        direccion = validated_data.pop('direccion', '')
        telefono_cliente = validated_data.pop('telefono', '')

        telefono_productor = validated_data.pop('telefono_productor', '')  # ya viene normalizado
        nombre_finca = validated_data.pop('nombre_finca', '')
        categorias_cultivo = validated_data.pop('categorias_cultivo', [])

        password = validated_data.pop('password')
        validated_data.pop('password2', None)

        # 🔥 normalizar email
        validated_data['email'] = (validated_data.get('email') or '').strip().lower()

        with transaction.atomic():
            user = User.objects.create_user(password=password, **validated_data)

            if user.rol == 'cliente':
                Cliente.objects.create(
                    usuario=user,
                    direccion=direccion,
                    telefono=telefono_cliente.strip(),
                    telefono_verificado=False
                )

            elif user.rol == 'productor':
                Productor.objects.create(
                    usuario=user,
                    telefono=telefono_productor.strip(),
                    nombre_finca=nombre_finca.strip(),
                    categorias_cultivo=",".join(categorias_cultivo)
                )

        return user
