# backend/coreapp/admin.py
from django.contrib import admin

from .models import Empleado, Pedido, PedidoItem, Producto

class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "precio", "activo")
    search_fields = ("nombre", "categoria")
    list_filter = ("activo", "categoria")


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "apellido", "email", "activo")
    search_fields = ("nombre", "apellido", "email")
    list_filter = ("activo",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente_nombre", "estado", "total", "empleado", "created_at")
    list_filter = ("estado", "created_at")
    search_fields = ("cliente_nombre", "cliente_email")
    inlines = [PedidoItemInline]

