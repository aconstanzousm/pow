# backend/coreapp/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EmpleadoViewSet,
    PedidoViewSet,
    ProductoViewSet,
    IndexView,
    MenuView,
    AboutUsView,
    CheckoutView,
    PaymentView,
    TestView,
    AdminLoginView,
    AdminPanelView,
    EmpleadoPanelView,
    login_view,
    cafe_status_view,
    estadisticas_view,
)


router = DefaultRouter()
# Sin prefijo "api/" — el JS llama a /pedidos/, /productos/, /empleados/
router.register(r"pedidos", PedidoViewSet, basename="pedido")
router.register(r"productos", ProductoViewSet, basename="producto")
router.register(r"empleados", EmpleadoViewSet, basename="empleado")


urlpatterns = [
    # Autenticación
    path("login/", login_view, name="login"),

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