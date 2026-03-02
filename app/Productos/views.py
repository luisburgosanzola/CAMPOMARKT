from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import FloatField
from django.db.models.functions import Cast
from app.Usuarios.models import User
from .models import Producto, Categoria, Oferta

from django.contrib.auth.decorators import login_required



from django.contrib import messages

from django.urls import reverse




# 📌 LISTAS DE PRODUCTOS VÁLIDOS POR CATEGORÍA (para el JS del front)
NOMBRES_VALIDOS = {
    'fruta': [
        'manzana', 'pera', 'mango', 'banano', 'platano', 'fresa', 'uva', 'piña', 'papaya', 'sandia',
        'melon', 'kiwi', 'maracuya', 'guanabana', 'lulo', 'curuba', 'feijoa', 'granadilla',
        'cereza', 'ciruela', 'durazno', 'nectarina', 'albaricoque', 'higo', 'frambuesa', 'mora',
        'arandano', 'limon', 'naranja', 'mandarina', 'toronja', 'pomelo', 'coco', 'chirimoya',
        'tamarindo', 'lichi', 'pitaya', 'dragonfruit', 'carambola', 'caqui', 'membrillo',
        'ananá', 'acerola', 'zapote', 'níspero', 'guayaba', 'jackfruit', 'durian',
        'physalis', 'uchuva', 'borojó', 'aguacate', 'tomate de arbol', 'tuna', 'pepino dulce',
        'mangostino', 'rambutan', 'longan', 'salak', 'camu camu'
    ],

    'verdura': [
        'lechuga', 'zanahoria', 'cebolla', 'tomate', 'pepino', 'espinaca', 'brocoli', 'coliflor',
        'repollo', 'acelga', 'apio', 'pimenton', 'aji', 'berenjena', 'calabacin', 'calabaza',
        'rabano', 'remolacha', 'nabo', 'arveja', 'habichuela', 'vainita', 'cilantro', 'perejil',
        'cebollin', 'puerro', 'champiñon', 'setas', 'endibia', 'escarola', 'alcachofa', 'okra',
        'chayote', 'tomate cherry', 'coles de bruselas', 'col rizada', 'kale', 'berro',
        'mostaza verde', 'oregano', 'menta', 'hierbabuena', 'diente de leon', 'tatsoi',
        'col china', 'pak choi', 'bok choy', 'cebolleta', 'hojas de mostaza',
        'cebolin chino', 'cilantro cimarron', 'cardo', 'hinojo', 'chirivia'
    ],

    'tuberculo': [
        'papa', 'yuca', 'ñame', 'arracacha', 'batata',
        'camote', 'malanga', 'oca', 'taro', 'mandioca',
        'boniato', 'ulluco', 'mashua', 'jicama', 'topinambur',
        'raiz de loto', 'raiz de maca', 'chirivia', 'salsifi'
    ],
}


# 📌 DEPARTAMENTOS → MUNICIPIOS (para el select dinámico)
DEPARTAMENTOS_MUNICIPIOS = {
    "Amazonas": ["Leticia", "Puerto Nariño", "Tarapacá"],
    "Antioquia": ["Medellín", "Bello", "Envigado", "Itagüí"],
    "Huila": [
        "Neiva", "Acevedo", "Agrado", "Aipe", "Algeciras", "Altamira", "Baraya",
        "Campoalegre", "Colombia", "Elías", "Garzón", "Gigante", "Guadalupe",
        "Hobo", "Íquira", "Isnos", "La Argentina", "La Plata", "Nátaga",
        "Oporapa", "Paicol", "Palestina", "Pital", "Pitalito", "Rivera",
        "Saladoblanco", "San Agustín", "Santa María", "Suaza", "Tarqui",
        "Tello", "Teruel", "Tesalia", "Timaná", "Villavieja", "Yaguará",
    ],
    "Cundinamarca": ["Bogotá", "Soacha", "Chía", "Zipaquirá"],
    "Valle del Cauca": ["Cali", "Palmira", "Buenaventura", "Tuluá"],
}


# ==========================
#   LISTAR PRODUCTOS (PÚBLICO)
# ==========================
def listar_productos(request):

    categorias = Categoria.objects.all()

    categoria_seleccionada = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda')
    orden = request.GET.get('orden')

    productos = Producto.objects.filter(estado="disponible")

    if categoria_seleccionada:
        productos = productos.filter(categoria__nombre__iexact=categoria_seleccionada)

    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda.strip())

    productos = productos.annotate(
        precio_num=Cast('precio_unitario', FloatField())
    )

    if orden == 'precio_asc':
        productos = productos.order_by('precio_num')
    elif orden == 'precio_desc':
        productos = productos.order_by('-precio_num')

    if request.user.is_authenticated:
        productos = productos.prefetch_related('favoritos')
        for p in productos:
            p.es_favorito_usuario = p.favoritos.filter(id=request.user.id).exists()
    else:
        for p in productos:
            p.es_favorito_usuario = False

    return render(request, 'productos_listar.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_seleccionada': categoria_seleccionada,
        'busqueda': busqueda,
        'orden': orden,
    })



# ==========================
#   AGREGAR PRODUCTO
# ==========================



# ... tus diccionarios NOMBRES_VALIDOS y DEPARTAMENTOS_MUNICIPIOS arriba ...

@login_required(login_url="login_page")
def agregar_producto(request):
    # ✅ BLOQUEO REAL: si no es productor, NO puede ni ver el formulario
    if getattr(request.user, "rol", None) != "productor":
        messages.error(request, "Solo los usuarios con rol PRODUCTOR pueden publicar productos.")
        return redirect("listar_productos")  # o "main_page"

    categorias = Categoria.objects.all()
    departamentos_municipios = DEPARTAMENTOS_MUNICIPIOS

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        categoria_id = request.POST.get("categoria")
        descripcion = request.POST.get("descripcion")

        unidad_medida = request.POST.get("unidad_medida")
        cantidad_disponible = request.POST.get("cantidad_disponible")
        precio_unitario = request.POST.get("precio_unitario")
        calidad = request.POST.get("calidad")
        estado = request.POST.get("estado") or "disponible"
        imagen_principal = request.FILES.get("imagen_principal")
        imagen_secundaria = request.FILES.get("imagen_secundaria")

        departamento = request.POST.get("departamento")
        municipio = request.POST.get("municipio")
        telefono = request.POST.get("telefono")
        fecha_disponibilidad = request.POST.get("fecha_disponibilidad")

        errores = []

        categoria = Categoria.objects.filter(id=categoria_id).first()
        if not categoria:
            errores.append("Debe seleccionar una categoría válida.")

        if not nombre:
            errores.append("El nombre no puede estar vacío.")

        if not unidad_medida:
            errores.append("Debe seleccionar una unidad de medida.")

        if not precio_unitario or not precio_unitario.replace(".", "", 1).isdigit():
            errores.append("El precio unitario debe ser numérico.")

        if not departamento:
            errores.append("Debe seleccionar un departamento.")

        if not municipio:
            errores.append("Debe seleccionar un municipio.")

        if errores:
            return render(request, "producto.html", {
                "categorias": categorias,
                "errores": errores,
                "form_data": request.POST,
                "departamentos_municipios": departamentos_municipios,
            })

        Producto.objects.create(
            productor=request.user,
            nombre=nombre,
            categoria=categoria,
            descripcion=descripcion,
            unidad_medida=unidad_medida,
            cantidad_disponible=cantidad_disponible,
            precio_unitario=precio_unitario,
            calidad=calidad,
            estado=estado,
            imagen_principal=imagen_principal,
            imagen_secundaria=imagen_secundaria,
            departamento=departamento,
            municipio=municipio,
            telefono=telefono,
            fecha_disponibilidad=fecha_disponibilidad or None,
        )

        messages.success(request, "✅ Producto publicado correctamente.")
        return redirect("listar_productos")

    return render(request, "producto.html", {
        "categorias": categorias,
        "departamentos_municipios": departamentos_municipios,
    })


# ==========================
#   DETALLE PRODUCTO (PÚBLICO)
# ==========================
@login_required(login_url="login_page")
def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    es_favorito = producto.favoritos.filter(id=request.user.id).exists()
    oferta_activa = Oferta.objects.filter(producto=producto, activa=True).first()

    return render(request, 'detalle_produc.html', {
        'producto': producto,
        'es_favorito': es_favorito,
        'oferta_activa': oferta_activa,
    })


# ==========================
#   MIS FAVORITOS
# ==========================
def mis_favoritos(request):
    if not request.user.is_authenticated:
        return redirect('login_page')

    productos = Producto.objects.filter(favoritos=request.user)

    return render(request, "product_favorito.html", {
        "productos_favoritos": productos,
    })


# ==========================
#   TOGGLE FAVORITO
# ==========================
from django.http import JsonResponse
from django.shortcuts import redirect

def toggle_favorito(request, producto_id):
    if not request.user.is_authenticated:
        # si es AJAX → JSON con 401
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"redirect": True, "url": reverse("login_page")}, status=401)

        return redirect('login_page')

    producto = get_object_or_404(Producto, id=producto_id)

    if producto.favoritos.filter(id=request.user.id).exists():
        producto.favoritos.remove(request.user)
        es_favorito = False
    else:
        producto.favoritos.add(request.user)
        es_favorito = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"es_favorito": es_favorito})

    return redirect('mis_favoritos')


from django.http import JsonResponse


# ==========================
#   FILTRAR PRODUCTOS (AJAX)
# ==========================
def filtrar_productos_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({"redirect": True, "url": reverse("login_page")}, status=401)

    categoria = request.GET.get('categoria', '').strip().lower()

    mapa = {
        'fruta': 'frutas',
        'verdura': 'verduras',
        'tuberculo': 'tuberculos',
    }
    categoria_bd = mapa.get(categoria, categoria)

    productos = Producto.objects.filter(
        categoria__nombre__iexact=categoria_bd
    )[:20]

    data = []
    for p in productos:
        data.append({
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio_unitario,
            "imagen": p.imagen_principal.url if p.imagen_principal else "",
            "unidad": p.get_unidad_medida_display() if hasattr(p, 'get_unidad_medida_display') else p.unidad_medida,
        })

    return JsonResponse({"productos": data})



# ==========================
#   NOSOTROS (PÚBLICO)
# ==========================
def nosotros(request):
    return render(request, 'nosotros.html')



from django.db.models import Q

def buscar_global(request):
    q = (request.GET.get("q") or "").strip()

    productos = Producto.objects.none()
    productores = User.objects.none()

    if q:
        # Productos
        productos = Producto.objects.filter(
            Q(nombre__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(categoria__nombre__icontains=q)
        ).distinct()

        # Productores (usuarios con rol productor)
        productores = User.objects.filter(
            rol="productor"
        ).filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        ).distinct()

    return render(request, "buscar.html", {
        "q": q,
        "productos": productos,
        "productores": productores,
    })


def perfil_productor_publico(request, username):
    productor = get_object_or_404(User, username=username, rol="productor")

    productos = Producto.objects.filter(
        productor=productor,
        estado="disponible"
    )

    return render(request, "perfil_productor.html", {
        "productor": productor,
        "productos": productos
    })




# ofertas

@login_required(login_url="login_page")
def crear_oferta(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    # ✅ Solo productor y dueño del producto
    if getattr(request.user, "rol", None) != "productor" or producto.productor_id != request.user.id:
        messages.error(request, "No tienes permisos para ofertar este producto.")
        return redirect("detalle_producto", producto_id=producto.id)

    # si ya existe oferta, la editamos
    oferta, _ = Oferta.objects.get_or_create(
        producto=producto,
        defaults={"productor": request.user, "precio_oferta": producto.precio_unitario or "0"}
    )

    if request.method == "POST":
        precio_oferta = (request.POST.get("precio_oferta") or "").strip()

        if not precio_oferta:
            messages.error(request, "Debes ingresar un precio de oferta.")
            return redirect("crear_oferta", producto_id=producto.id)

        oferta.precio_oferta = precio_oferta
        oferta.activa = True
        oferta.productor = request.user
        oferta.save()

        messages.success(request, "🔥 Oferta guardada y publicada.")
        return redirect("detalle_producto", producto_id=producto.id)

    return render(request, "crear_oferta.html", {"producto": producto, "oferta": oferta})


def listar_ofertas(request):
    ofertas = Oferta.objects.filter(activa=True).select_related("producto", "productor").order_by("-creada_en")
    return render(request, "ofertas.html", {"ofertas": ofertas})



@login_required(login_url="login_page")
def quitar_oferta(request, oferta_id):
    oferta = get_object_or_404(Oferta, id=oferta_id)

    # ✅ Solo productor y dueño de la oferta
    if getattr(request.user, "rol", None) != "productor" or oferta.productor_id != request.user.id:
        messages.error(request, "No tienes permisos para quitar esta oferta.")
        return redirect("listar_ofertas")

    if request.method == "POST":
        oferta.activa = False
        oferta.save()
        messages.success(request, "✅ Oferta quitada.")
        return redirect("detalle_producto", producto_id=oferta.producto.id)

    return redirect("listar_ofertas")