from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Empleado, Pedido, PedidoItem, Producto


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
        user = User.objects.create(username=username, email=validated_data.get("email", ""))
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()

        empleado = Empleado.objects.create(user=user, **validated_data)
        return empleado


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ("id", "nombre", "descripcion", "precio", "categoria", "activo", "created_at", "updated_at")


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
        read_only_fields = ("total", "created_at", "updated_at")

    def get_empleado_nombre(self, obj):
        if not obj.empleado_id:
            return None
        return f"{obj.empleado.nombre} {obj.empleado.apellido}".strip()

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        empleado_id = validated_data.pop("empleado_id", None)

        pedido = Pedido.objects.create(**validated_data)
        if empleado_id:
            pedido.empleado_id = empleado_id
            pedido.save(update_fields=["empleado"])

        total = 0
        for item in items_data:
            producto_id = item.pop("producto_id", None)
            producto = None
            if producto_id:
                producto = Producto.objects.filter(id=producto_id).first()
            if producto:
                nombre = producto.nombre
                precio = producto.precio
            else:
                nombre = item.get("nombre", "")
                precio = int(item.get("precio", 0))
            cantidad = int(item.get("cantidad", 1))
            total += precio * cantidad
            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                nombre=nombre,
                precio=precio,
                cantidad=cantidad,
            )

        pedido.total = total
        pedido.save(update_fields=["total"])
        return pedido

    def update(self, instance, validated_data):
        empleado_id = validated_data.pop("empleado_id", None) if "empleado_id" in validated_data else None
        items_data = validated_data.pop("items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if empleado_id is not None:
            instance.empleado_id = empleado_id

        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            total = 0
            for item in items_data:
                producto_id = item.pop("producto_id", None)
                producto = None
                if producto_id:
                    producto = Producto.objects.filter(id=producto_id).first()
                if producto:
                    nombre = producto.nombre
                    precio = producto.precio
                else:
                    nombre = item.get("nombre", "")
                    precio = int(item.get("precio", 0))
                cantidad = int(item.get("cantidad", 1))
                total += precio * cantidad
                PedidoItem.objects.create(
                    pedido=instance,
                    producto=producto,
                    nombre=nombre,
                    precio=precio,
                    cantidad=cantidad,
                )
            instance.total = total
            instance.save(update_fields=["total"])

        return instance

