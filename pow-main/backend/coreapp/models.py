from django.conf import settings
from django.db import models


class Empleado(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="empleado_profile",
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=255, blank=True)
    precio = models.PositiveIntegerField()
    categoria = models.CharField(max_length=60, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.nombre


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PREPARANDO = "preparando", "Preparando"
        LISTO = "listo", "Listo"
        CANCELADO = "cancelado", "Cancelado"

    cliente_nombre = models.CharField(max_length=150)
    cliente_email = models.EmailField(blank=True)
    nota = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    total = models.PositiveIntegerField(default=0)
    empleado = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Pedido #{self.id}"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, null=True, blank=True, on_delete=models.SET_NULL)
    nombre = models.CharField(max_length=150)
    precio = models.PositiveIntegerField()
    cantidad = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.nombre} x{self.cantidad}"

