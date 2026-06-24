from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import CafeConfig, Empleado, Pedido, Producto


class PedidoApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_user(
            username="admin_test",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.employee_user = self.user_model.objects.create_user(
            username="empleado_test",
            password="emp123",
        )
        self.empleado = Empleado.objects.create(
            user=self.employee_user,
            nombre="Ana",
            apellido="Barista",
            email="ana@example.com",
        )

        config = CafeConfig.get()
        config.abierto = True
        config.save()

    def test_create_order_discounts_stock_for_producto_items(self):
        producto = Producto.objects.create(
            nombre="Latte",
            descripcion="Cafe con leche",
            precio=3500,
            categoria="Cafés",
            activo=True,
            stock=5,
            stock_minimo=1,
        )

        response = self.client.post(
            "/pedidos/",
            {
                "cliente_nombre": "Seba",
                "items": [{"producto_id": producto.id, "cantidad": 2}],
            },
            format="json",
        )

        producto.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total"], 7000)
        self.assertTrue(response.data["codigo_pedido"].startswith("PED-"))
        self.assertEqual(producto.stock, 3)

    def test_create_order_rejects_when_stock_is_insufficient(self):
        producto = Producto.objects.create(
            nombre="Brownie",
            descripcion="Chocolate",
            precio=2500,
            categoria="Dulces",
            activo=True,
            stock=1,
            stock_minimo=1,
        )

        response = self.client.post(
            "/pedidos/",
            {
                "cliente_nombre": "Seba",
                "items": [{"producto_id": producto.id, "cantidad": 2}],
            },
            format="json",
        )

        producto.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(producto.stock, 1)

    def test_employee_only_can_update_order_status(self):
        pedido = Pedido.objects.create(cliente_nombre="Cliente", total=1000)

        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/pedidos/{pedido.id}/",
            {"cliente_nombre": "Cambio no permitido"},
            format="json",
        )

        pedido.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(pedido.cliente_nombre, "Cliente")

    def test_cafe_status_accepts_false_string(self):
        config = CafeConfig.get()
        config.abierto = True
        config.save()

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            "/cafe-status/",
            {"abierto": "false"},
            format="json",
        )

        config.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(config.abierto)
