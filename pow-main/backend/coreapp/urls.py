from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EmpleadoViewSet, PedidoViewSet, ProductoViewSet


router = DefaultRouter()
router.register(r"empleados", EmpleadoViewSet, basename="empleado")
router.register(r"productos", ProductoViewSet, basename="producto")
router.register(r"pedidos", PedidoViewSet, basename="pedido")


urlpatterns = [
    path("", include(router.urls)),
]

