from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_productos, name='listar_productos'),
    path('agregar/', views.agregar_producto, name='agregar_producto'),
    path('favoritos/', views.mis_favoritos, name='mis_favoritos'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('ajax-filtrar/', views.filtrar_productos_ajax, name='ajax_filtrar'),
    path('<int:producto_id>/favorito/', views.toggle_favorito, name='toggle_favorito'),
    path('<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('ofertas/', views.listar_ofertas, name='listar_ofertas'),
    path('<int:producto_id>/ofertar/', views.crear_oferta, name='crear_oferta'),
    path('ofertas/quitar/<int:oferta_id>/', views.quitar_oferta, name='quitar_oferta'),

]

