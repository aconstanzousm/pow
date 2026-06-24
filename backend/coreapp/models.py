# backend/coreapp/models.py
from django.conf import settings
from django.db import models
import secrets

def generate_codigo_pedido() -> str:
    return f"PED-{secrets.token_hex(3).upper()}"


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

class Cliente(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cliente_profile",
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True)
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
    imagen = models.ImageField(upload_to="productos/", null=True, blank=True)
    stock = models.IntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
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
    codigo_pedido = models.CharField(max_length=10, unique=True, db_index=True, editable=False)
    cliente_email = models.EmailField(blank=True)
    nota = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    total = models.PositiveIntegerField(default=0)
    empleado = models.ForeignKey(Empleado, null=True, blank=True, on_delete=models.SET_NULL)
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL, related_name="pedidos")
    session_key = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.codigo_pedido:
            codigo = generate_codigo_pedido()
            while Pedido.objects.filter(codigo_pedido=codigo).exists():
                codigo = generate_codigo_pedido()
            self.codigo_pedido = codigo
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.codigo_pedido} - {self.cliente_nombre}"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, null=True, blank=True, on_delete=models.SET_NULL)
    nombre = models.CharField(max_length=150)
    precio = models.PositiveIntegerField()
    cantidad = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.nombre} x{self.cantidad}"

class CafeConfig(models.Model):
    """Singleton: configuración global del café."""
    abierto = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Café"

    def save(self, *args, **kwargs):
        self.pk = 1  # Forzar singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Abierto" if self.abierto else "Cerrado"
