# backend/coreapp/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EmpleadoViewSet, PedidoViewSet, ProductoViewSet,
    IndexView, MenuView, AboutUsView, CheckoutView, PaymentView, TestView,
    AdminLoginView, AdminPanelView, EmpleadoPanelView,
    LoginClienteView, MisPedidosView, ReciboView,
    login_view, cafe_status_view, estadisticas_view,
    cliente_registro_view, cliente_login_view, mis_pedidos_view, recibo_pedido_view,
)


router = DefaultRouter()
# Sin prefijo "api/" — el JS llama a /pedidos/, /productos/, /empleados/
router.register(r"pedidos", PedidoViewSet, basename="pedido")
router.register(r"productos", ProductoViewSet, basename="producto")
router.register(r"empleados", EmpleadoViewSet, basename="empleado")


urlpatterns = [
    # Autenticación
    path("login/", login_view, name="login"),
    # Cliente — auth y datos
    path("clientes/registro/", cliente_registro_view, name="cliente-registro"),
    path("clientes/login/", cliente_login_view, name="cliente-login"),
    path("mis-pedidos-data/", mis_pedidos_view, name="mis-pedidos-data"),
    path("recibo-data/<str:codigo>/", recibo_pedido_view, name="recibo-data"),

    # Cliente — páginas
    path("login-cliente/", LoginClienteView.as_view(), name="login-cliente"),
    path("mis-pedidos/", MisPedidosView.as_view(), name="mis-pedidos"),
    path("recibo/<str:codigo>/", ReciboView.as_view(), name="recibo"),
    path("login-cliente.html", LoginClienteView.as_view(), name="login-cliente-html"),
    path("mis-pedidos.html", MisPedidosView.as_view(), name="mis-pedidos-html"),

    # Páginas frontend — URLs limpias
    path("", IndexView.as_view(), name="index"),
    path("menu/", MenuView.as_view(), name="menu"),
    path("aboutus/", AboutUsView.as_view(), name="aboutus"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("payment/", PaymentView.as_view(), name="payment"),
    path("test/", TestView.as_view(), name="test"),
    path("admin-login/", AdminLoginView.as_view(), name="admin-login"),
    path("admin-panel/", AdminPanelView.as_view(), name="admin-panel"),
    path("empleado-panel/", EmpleadoPanelView.as_view(), name="empleado-panel"),
    path("cafe-status/", cafe_status_view, name="cafe-status"),
    path("estadisticas/", estadisticas_view, name="estadisticas"),

    # Páginas frontend — URLs con .html (para links directos en el HTML)
    path("index.html", IndexView.as_view(), name="index-html"),
    path("menu.html", MenuView.as_view(), name="menu-html"),
    path("aboutus.html", AboutUsView.as_view(), name="aboutus-html"),
    path("checkout.html", CheckoutView.as_view(), name="checkout-html"),
    path("payment.html", PaymentView.as_view(), name="payment-html"),
    path("test.html", TestView.as_view(), name="test-html"),
    path("admin/admin-login.html", AdminLoginView.as_view(), name="admin-login-html"),
    path("admin/admin-panel.html", AdminPanelView.as_view(), name="admin-panel-html"),
    path("admin/empleado-panel.html", EmpleadoPanelView.as_view(), name="empleado-panel-html"),

    # Rutas de la API
    path("", include(router.urls)),
]