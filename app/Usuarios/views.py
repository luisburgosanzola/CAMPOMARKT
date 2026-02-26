from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ClienteSerializer,
    ProductorSerializer,
)

from .models import CodigoSMS, Cliente, Productor
from .utils import enviar_sms_verificacion

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages


# =====================================================
# 🔵 GOOGLE — SELECCIONAR ROL DESPUÉS DEL LOGIN
# =====================================================

@login_required
def seleccionar_rol_google(request):
    # Si ya tiene rol, no debe volver aquí
    if request.user.rol in ["cliente", "productor"]:
        return redirect('main_page')

    if request.method == 'POST':
        rol = request.POST.get('rol')

        if rol == 'cliente':
            request.user.rol = 'cliente'
            request.user.save()
            return redirect('completar_cliente')

        elif rol == 'productor':
            request.user.rol = 'productor'
            request.user.save()
            return redirect('completar_productor')

        else:
            messages.error(request, "Debes seleccionar una opción válida.")

    return render(request, 'seleccionar_rol_google.html')


@login_required
def google_completo(request):
    """
    Después de iniciar sesión con Google:
    - Si no tiene rol → seleccionar rol
    - Si tiene rol pero no perfil → completar perfil
    - Si ya tiene todo → main
    """
    user = request.user

    if not user.rol:
        return redirect('seleccionar_rol_google')

    if user.rol == "cliente" and not hasattr(user, "cliente"):
        return redirect('completar_cliente')

    if user.rol == "productor" and not hasattr(user, "productor"):
        return redirect('completar_productor')

    return redirect('main_page')


# =====================================================
# 🧍 COMPLETAR PERFIL CLIENTE
# =====================================================

@login_required
def completar_cliente(request):
    if request.user.rol != 'cliente':
        return redirect('main_page')

    cliente, _ = Cliente.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')

        if not direccion or not telefono:
            messages.error(request, "Todos los campos son obligatorios.")
        else:
            cliente.direccion = direccion
            cliente.telefono = telefono
            cliente.save()
            messages.success(request, "Perfil de cliente completado correctamente.")
            return redirect('main_page')

    return render(request, 'completar_cliente.html', {'cliente': cliente})


# =====================================================
# 🌱 COMPLETAR PERFIL PRODUCTOR
# =====================================================

@login_required
def completar_productor(request):
    if request.user.rol != 'productor':
        return redirect('main_page')

    productor, _ = Productor.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        nombre_finca = request.POST.get('nombre_finca')
        tipo_cultivo = request.POST.get('tipo_cultivo')

        if not nombre_finca or not tipo_cultivo:
            messages.error(request, "Todos los campos son obligatorios.")
        else:
            productor.nombre_finca = nombre_finca
            productor.tipo_cultivo = tipo_cultivo
            productor.save()
            messages.success(request, "Perfil de productor completado correctamente.")
            return redirect('main_page')

    return render(request, 'completar_productor.html', {'productor': productor})


# =====================================================
# 🟢 1. ENVIAR CÓDIGO SMS
# =====================================================

class EnviarCodigoSMSView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        telefono = request.data.get("telefono")

        if not telefono:
            return Response(
                {"detail": "El teléfono es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        codigo_obj, _ = CodigoSMS.objects.get_or_create(telefono=telefono)
        codigo_obj.generar_codigo()

        enviar_sms_verificacion(telefono, codigo_obj.codigo)

        return Response(
            {"detail": "Código enviado correctamente."},
            status=status.HTTP_200_OK
        )


# =====================================================
# 🟢 2. REGISTRO CON VALIDACIÓN DE CÓDIGO SMS
# =====================================================

class RegisterJWTView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        telefono = request.data.get("telefono")
        codigo_sms = request.data.get("codigo_sms")

        if not telefono or not codigo_sms:
            return Response(
                {"detail": "Faltan datos: teléfono y código_sms son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            codigo_obj = CodigoSMS.objects.get(telefono=telefono)
        except CodigoSMS.DoesNotExist:
            return Response(
                {"detail": "No se ha enviado ningún código a este teléfono."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if codigo_obj.codigo != codigo_sms:
            return Response(
                {"detail": "El código SMS es incorrecto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Crear perfil automático según rol
        if user.rol == "cliente":
            Cliente.objects.get_or_create(usuario=user, telefono=telefono)

        elif user.rol == "productor":
            Productor.objects.get_or_create(usuario=user)

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


# =====================================================
# 🟢 3. PERFIL DEL USUARIO (API)
# =====================================================

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.rol == "cliente" and hasattr(user, "cliente"):
            perfil_data = ClienteSerializer(user.cliente).data

        elif user.rol == "productor" and hasattr(user, "productor"):
            perfil_data = ProductorSerializer(user.productor).data

        else:
            return Response({"detail": "Perfil no encontrado"}, status=404)

        return Response({
            "user": UserSerializer(user).data,
            "perfil": perfil_data
        })
