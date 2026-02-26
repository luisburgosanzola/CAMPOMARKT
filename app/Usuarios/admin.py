from django.contrib import admin
from .models import User, Cliente, Productor


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'rol', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('rol', 'is_active', 'is_staff')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'direccion', 'telefono')
    search_fields = ('usuario__username', 'direccion', 'telefono')
    list_filter = ('usuario__rol',)


@admin.register(Productor)
class ProductorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nombre_finca', 'telefono', 'categorias_cultivo')
    search_fields = ('usuario__username', 'nombre_finca', 'telefono')
    list_filter = ('usuario__rol', 'categorias_cultivo')
