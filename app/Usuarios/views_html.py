from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from functools import wraps
from .models import CodigoEmail
from .utils import enviar_codigo_email

from allauth.account.models import EmailAddress

from .serializers import RegisterSerializer
from .models import Cliente, Productor
from app.Productos.models import Producto

from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required





User = get_user_model()






# =====================================================
# 🔐 PERFIL COMPLETO
# =====================================================
def _user_has_complete_profile(user):
    """
    Para Google (Opción B):
    - Si el usuario está autenticado
    - Y tiene rol asignado (cliente o productor)
    => se considera perfil válido y puede entrar al main
    """

    if not user.is_authenticated:
        return False

    if user.rol in ["cliente", "productor"]:
        return True

    return False


# =====================================================
# 🏠 MAIN
# =====================================================
def _user_has_complete_profile(user):
    return bool(user.is_authenticated and user.rol in ["cliente", "productor"])


def main_page(request):
    if request.user.is_authenticated and not _user_has_complete_profile(request.user):
        return redirect("seleccionar_rol_google")
    return render(request, "main.html")







# =====================================================
# 🔓 LOGIN
# =====================================================
@csrf_protect
def login_page(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "Credenciales inválidas.")
            return render(request, "Registro/login.html")

        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            messages.error(request, "Credenciales inválidas.")
            return render(request, "Registro/login.html")

        # 🔍 Verificar si el correo está confirmado
        email_ok = EmailAddress.objects.filter(
            user=user,
            email__iexact=user.email,
            verified=True
        ).exists()

        if not email_ok:
            request.session["verify_user_id"] = user.id

            # ✅ Normalizar email SIEMPRE
            email_clean = (user.email or "").strip().lower()
            if user.email != email_clean:
                user.email = email_clean
                user.save(update_fields=["email"])

            # 🔐 Generar nuevo código
            codigo = CodigoEmail.generar()
            CodigoEmail.objects.create(
                user=user,
                email=email_clean,
                codigo=codigo
            )

            print("📨 Enviando OTP a =>", repr(email_clean))
            enviar_codigo_email(email_clean, codigo)

            messages.warning(request, "Debes verificar tu correo para entrar.")
            return redirect("verify_email")

        # ✅ Si está verificado → login normal
        auth_login(request, user)
        return redirect("main_page")

    return render(request, "Registro/login.html")


# =====================================================
# 📝 REGISTRO
# =====================================================
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.contrib import messages

@csrf_protect
def register_page(request):
    if request.method == "POST":
        data = request.POST.copy()

        # ✅ agarrar lista de checkboxes
        categorias = request.POST.getlist("categorias_cultivo")
        data.setlist("categorias_cultivo", categorias)

        serializer = RegisterSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save()

            # 🔥 NORMALIZAR EMAIL
            user.email = (user.email or "").strip().lower()
            user.save(update_fields=["email"])

            codigo = CodigoEmail.generar()
            CodigoEmail.objects.create(user=user, email=user.email, codigo=codigo)

            enviar_codigo_email(user.email, codigo)

            request.session["verify_user_id"] = user.id
            messages.success(request, "Te enviamos un código a tu correo.")
            return redirect("verify_email")

        # ❌ SI NO ES VÁLIDO: mostrar errores
        print("❌ serializer.errors =>", serializer.errors)
        messages.error(request, "Formulario inválido, revisa los campos.")

        return render(request, "Registro/register.html", {
            "errors": serializer.errors,
            "selected_categorias": categorias,  # ✅ para que no se pierdan checks
        })

    return render(request, "Registro/register.html", {"selected_categorias": []})


# =====================================================
# 🚪 LOGOUT
# =====================================================
def logout_page(request):
    logout(request)
    messages.success(request, "👋 Has cerrado sesión. ¡Vuelve pronto!")
    return redirect("main_page")
# =====================================================
# 👤 PERFIL
# =====================================================
@login_required(login_url="login_page")
def profile_page(request):
    user = request.user
    editable = request.GET.get("editar") == "true"

    perfil = None
    template = "perfiles/cliente.html"
    productos = None  # 👈 AGREGA ESTO

    if user.rol == "cliente":
        perfil, _ = Cliente.objects.get_or_create(usuario=user)
        template = "perfiles/cliente.html"

    elif user.rol == "productor":
        perfil, _ = Productor.objects.get_or_create(usuario=user)
        template = "perfiles/productor.html"

        # 🔥 AQUÍ TRAEMOS LOS PRODUCTOS
        productos = Producto.objects.filter(
            productor=user
        ).order_by("-fecha_publicacion")

    else:
        messages.error(request, "No tienes rol asignado.")
        return redirect("main_page")

    if request.method == "POST":
        # ======= FOTO (para ambos) =======
        if editable and request.FILES.get("profile_image"):
            user.profile_image = request.FILES["profile_image"]
            user.save()

        # ======= DATOS USER =======
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.save()

        # ======= DATOS PERFIL SEGÚN ROL =======
        if user.rol == "cliente":
            perfil.direccion = request.POST.get("direccion", perfil.direccion)
            perfil.telefono = request.POST.get("telefono", perfil.telefono)
            perfil.save()

        elif user.rol == "productor":
            perfil.nombre_finca = request.POST.get("nombre_finca", perfil.nombre_finca)
            perfil.categorias_cultivo = request.POST.get("categorias_cultivo", perfil.categorias_cultivo)
            perfil.telefono = request.POST.get("telefono", perfil.telefono)
            perfil.save()

        messages.success(request, "✅ Perfil actualizado correctamente.")
        return redirect("mi_perfil")

    return render(request, template, {
            "perfil": perfil,
            "editable": editable,
            "productos": productos,  # 👈 ENVÍALO AL TEMPLATE
        })
# =====================================================
# 🔵 GOOGLE POST LOGIN
# =====================================================

@login_required(login_url="login_page")
def google_completo(request):
    if request.user.rol in ["cliente", "productor"]:
        return redirect("main_page")
    return redirect("seleccionar_rol_google")





# =====================================================
# 🧩 SELECCIONAR ROL
# =====================================================
@login_required(login_url="login_page")
def seleccionar_rol_google(request):
    if request.method == "POST":
        rol = request.POST.get("rol")

        if rol not in ["cliente", "productor"]:
            messages.error(request, "Rol inválido.")
            return render(request, "Registro/seleccionar_rol_google.html")

        request.user.rol = rol
        request.user.save()

        return redirect(
            "completar_cliente" if rol == "cliente" else "completar_productor"
        )

    return render(request, "Registro/seleccionar_rol_google.html")



# =====================================================
# 🧍 CLIENTE
# =====================================================
@login_required(login_url="login_page")


def completar_cliente(request):
    if request.user.rol != "cliente":
        return redirect("main_page")

    if request.method == "POST":
        direccion = request.POST.get("direccion")
        telefono = request.POST.get("telefono")

        if not direccion or not telefono:
            messages.error(request, "Campos obligatorios.")
        else:
            Cliente.objects.update_or_create(
                usuario=request.user,
                defaults={"direccion": direccion, "telefono": telefono}
            )
            return redirect("main_page")

    return render(request, "Registro/completar_cliente.html")



# =====================================================
# 🌱 PRODUCTOR
# =====================================================
@login_required(login_url="login_page")

def completar_productor(request):
    if request.user.rol != "productor":
        return redirect("main_page")

    if request.method == "POST":
        telefono = request.POST.get("telefono")
        nombre_finca = request.POST.get("nombre_finca")

        # 👇 AQUÍ VA LO NUEVO
        categorias = request.POST.getlist("categorias_cultivo")
        categorias_str = ",".join(categorias)

        if not telefono or not nombre_finca or not categorias:
            messages.error(request, "Todos los campos son obligatorios.")
        else:
            Productor.objects.update_or_create(
                usuario=request.user,
                defaults={
                    "telefono": telefono,
                    "nombre_finca": nombre_finca,
                    "categorias_cultivo": categorias_str
                }
            )
            messages.success(request, "Perfil completado correctamente.")
            return redirect("main_page")

    return render(request, "Registro/completar_productor.html")





AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


@ensure_csrf_cookie
@csrf_protect
def verify_email(request):
    user_id = request.session.get("verify_user_id")
    if not user_id:
        messages.error(request, "No hay verificación pendiente.")
        return redirect("register_page")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.pop("verify_user_id", None)
        messages.error(request, "Usuario no encontrado.")
        return redirect("register_page")

    # ✅ Normalizar email SIEMPRE
    email = (user.email or "").strip().lower()
    if user.email != email:
        user.email = email
        user.save(update_fields=["email"])

    if request.method == "POST":
        action = request.POST.get("action")

        # ✅ Reenviar
        if action == "resend":
            codigo = CodigoEmail.generar()
            CodigoEmail.objects.create(user=user, email=email, codigo=codigo)

            print("📨 REENVIANDO OTP A =>", repr(email))
            enviar_codigo_email(email, codigo)

            messages.success(request, "Te reenviamos un código nuevo al correo.")
            return redirect("verify_email")

        # ✅ Verificar
        codigo_ingresado = (request.POST.get("code") or "").strip()

        try:
            obj = CodigoEmail.objects.filter(user=user, usado=False).latest("creado")
        except CodigoEmail.DoesNotExist:
            messages.error(request, "No hay código activo. Reenvía uno nuevo.")
            return render(request, "Registro/verify_email.html", {"email": email})

        if obj.esta_vencido():
            messages.error(request, "El código venció. Reenvía uno nuevo.")
            return render(request, "Registro/verify_email.html", {"email": email})

        if obj.codigo != codigo_ingresado:
            messages.error(request, "Código incorrecto.")
            return render(request, "Registro/verify_email.html", {"email": email})

        # Marcar usado
        obj.usado = True
        obj.save()

        # ✅ Marcar email verificado (allauth) usando email normalizado
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True}
        )

        # ✅ Login
        auth_login(request, user, backend=AUTH_BACKEND)

        # limpiar sesión
        request.session.pop("verify_user_id", None)

        messages.success(request, "✅ Correo verificado. Bienvenido.")
        return redirect("main_page")

    return render(request, "Registro/verify_email.html", {"email": email})


from allauth.socialaccount.providers.google.views import oauth2_login

def google_signup_start(request):
    # Bandera para permitir signup con Google
    request.session["allow_google_signup"] = True
    return oauth2_login(request)



from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from .models import Productor
from app.Productos.models import Producto

User = get_user_model()

def perfil_productor_publico(request, username):
    productor_user = get_object_or_404(User, username=username, rol="productor")
    perfil = get_object_or_404(Productor, usuario=productor_user)

    productos = Producto.objects.filter(productor=productor_user).order_by("-fecha_publicacion")

    return render(request, "perfiles/productor.html", {
        "productor_user": productor_user,
        "perfil": perfil,
        "productos": productos,
        "editable": False,
        "es_publico": True,
    })