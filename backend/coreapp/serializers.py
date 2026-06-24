# backend/coreapp/serializers.py
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Empleado, Pedido, PedidoItem, Producto, Cliente
from .models import CafeConfig


class EmpleadoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Empleado
        fields = ("id", "nombre", "apellido", "email", "telefono", "activo", "username", "password", "created_at", "updated_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["username"] = instance.user.username if instance.user else ""
        data.pop("password", None)
        return data

    def create(self, validated_data):
        username = (validated_data.pop("username", None) or "").strip()
        password = validated_data.pop("password", None)

        if not username or not password:
            raise serializers.ValidationError({"detail": "Falta username o password."})

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Ese nombre de usuario ya existe."})
        user = User.objects.create(username=username, email=validated_data.get("email", ""))
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()

        empleado = Empleado.objects.create(user=user, **validated_data)
        return empleado

class ClienteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Cliente
        fields = ("id", "nombre", "apellido", "email", "telefono", "username", "password", "created_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["username"] = instance.user.username if instance.user else ""
        data.pop("password", None)
        return data

    def create(self, validated_data):
        username = (validated_data.pop("username", None) or "").strip()
        password = validated_data.pop("password", None)

        if not username or not password:
            raise serializers.ValidationError({"detail": "Falta username o password."})

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Ese nombre de usuario ya existe."})
        if Cliente.objects.filter(email__iexact=validated_data.get("email", "")).exists():
            raise serializers.ValidationError({"email": "Ya existe una cuenta con ese correo."})

        user = User.objects.create(username=username, email=validated_data.get("email", ""))
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()

        cliente = Cliente.objects.create(user=user, **validated_data)
        return cliente

class ProductoSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(required=False, allow_null=True, use_url=True)
    bajo_stock = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id", "nombre", "descripcion", "precio", "categoria", "activo",
            "imagen", "stock", "stock_minimo", "bajo_stock",
            "created_at", "updated_at",
        )

    def get_bajo_stock(self, obj):
        return obj.stock <= obj.stock_minimo


class PedidoItemSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(required=False, allow_null=True)
    nombre = serializers.CharField(required=False, allow_blank=True)
    precio = serializers.IntegerField(required=False)

    class Meta:
        model = PedidoItem
        fields = ("id", "producto_id", "nombre", "precio", "cantidad")


class PedidoSerializer(serializers.ModelSerializer):
    items = PedidoItemSerializer(many=True)
    empleado_id = serializers.IntegerField(required=False, allow_null=True)
    empleado_nombre = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Pedido
        fields = (
            "id",
            "codigo_pedido",
            "cliente_nombre",
            "cliente_email",
            "nota",
            "estado",
            "total",
            "empleado_id",
            "empleado_nombre",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("codigo_pedido", "total", "created_at", "updated_at")

    def get_empleado_nombre(self, obj):
        if not obj.empleado_id:
            return None
        return f"{obj.empleado.nombre} {obj.empleado.apellido}".strip()

    def validate(self, attrs):
        items = attrs.get("items")
        if self.instance is None and not items:
            raise serializers.ValidationError({"items": "Debes agregar al menos un producto al pedido."})
        return attrs

    def _get_empleado(self, empleado_id):
        if empleado_id is None:
            return None
        empleado = Empleado.objects.filter(id=empleado_id).first()
        if not empleado:
            raise serializers.ValidationError({"empleado_id": "El empleado indicado no existe."})
        return empleado

    def _build_items_payload(self, items_data):
        if not items_data:
            raise serializers.ValidationError({"items": "Debes agregar al menos un producto al pedido."})

        payload = []
        required_stock = {}
        total = 0

        for item in items_data:
            producto_id = item.get("producto_id")
            producto = None

            try:
                cantidad = int(item.get("cantidad", 1))
            except (TypeError, ValueError):
                raise serializers.ValidationError({"items": 'La cantidad de cada item debe ser un entero.'})

            if cantidad <= 0:
                raise serializers.ValidationError({"items": "La cantidad de cada item debe ser mayor a 0."})

            if producto_id:
                producto = Producto.objects.filter(id=producto_id, activo=True).first()
                if not producto:
                    raise serializers.ValidationError({"items": f"El producto {producto_id} no existe o está inactivo."})
                nombre = producto.nombre
                precio = producto.precio
                required_stock[producto_id] = required_stock.get(producto_id, 0) + cantidad
            else:
                nombre = (item.get("nombre", "") or "").strip()
                if not nombre:
                    raise serializers.ValidationError({"items": "Cada item manual debe incluir un nombre."})
                try:
                    precio = int(item.get("precio", 0))
                except (TypeError, ValueError):
                    raise serializers.ValidationError({"items": "El precio de cada item debe ser un entero."})
                if precio < 0:
                    raise serializers.ValidationError({"items": "El precio de cada item no puede ser negativo."})

            total += precio * cantidad
            payload.append(
                {
                    "producto": producto,
                    "nombre": nombre,
                    "precio": precio,
                    "cantidad": cantidad,
                }
            )

        return payload, required_stock, total

    def _lock_products(self, product_ids):
        if not product_ids:
            return {}
        productos = Producto.objects.select_for_update().filter(id__in=product_ids)
        return {producto.id: producto for producto in productos}

    def _apply_stock_changes(self, previous_stock, next_stock):
        product_ids = set(previous_stock) | set(next_stock)
        locked_products = self._lock_products(product_ids)

        for product_id in product_ids:
            producto = locked_products.get(product_id)
            if not producto:
                raise serializers.ValidationError({"items": f"El producto {product_id} no existe."})

            delta = next_stock.get(product_id, 0) - previous_stock.get(product_id, 0)
            if delta > 0 and producto.stock < delta:
                raise serializers.ValidationError(
                    {"items": f'Stock insuficiente para "{producto.nombre}". Disponible: {producto.stock}.'}
                )

        for product_id in product_ids:
            producto = locked_products[product_id]
            delta = next_stock.get(product_id, 0) - previous_stock.get(product_id, 0)
            if delta != 0:
                producto.stock -= delta
                producto.save(update_fields=["stock"])

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        empleado_id = validated_data.pop("empleado_id", None)
        empleado = self._get_empleado(empleado_id)
        items_payload, required_stock, total = self._build_items_payload(items_data)

        with transaction.atomic():
            self._apply_stock_changes({}, required_stock)
            pedido = Pedido.objects.create(empleado=empleado, total=total, **validated_data)
            for item in items_payload:
                PedidoItem.objects.create(pedido=pedido, **item)

        return pedido

    def update(self, instance, validated_data):
        empleado_id = validated_data.pop("empleado_id", None) if "empleado_id" in validated_data else None
        items_data = validated_data.pop("items", None)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            if empleado_id is not None:
                instance.empleado = self._get_empleado(empleado_id)

            if items_data is not None:
                items_payload, required_stock, total = self._build_items_payload(items_data)
                previous_stock = {}
                for order_item in instance.items.select_related("producto").all():
                    if order_item.producto_id:
                        previous_stock[order_item.producto_id] = previous_stock.get(order_item.producto_id, 0) + order_item.cantidad

                self._apply_stock_changes(previous_stock, required_stock)
                instance.items.all().delete()
                for item in items_payload:
                    PedidoItem.objects.create(pedido=instance, **item)
                instance.total = total

            instance.save()

        return instance

class CafeConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CafeConfig
        fields = ("abierto", "updated_at")
        read_only_fields = ("updated_at",)
