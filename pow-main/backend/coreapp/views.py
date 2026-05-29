from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Empleado, Pedido, Producto
from .serializers import EmpleadoSerializer, PedidoSerializer, ProductoSerializer


class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.select_related("user").all().order_by("-id")
    serializer_class = EmpleadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_staff:
            raise PermissionDenied()
        return super().get_queryset()

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied()
        user = instance.user
        super().perform_destroy(instance)
        if user:
            user.delete()


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by("-id")
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied()
        serializer.save()

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise PermissionDenied()
        super().perform_destroy(instance)


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.prefetch_related("items").select_related("empleado").all().order_by("-id")
    serializer_class = PedidoSerializer

    def get_permissions(self):
        if getattr(self, "action", "") == "create":
            return [permissions.AllowAny()]
        if getattr(self, "action", "") == "destroy":
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        user = getattr(self.request, "user", None)
        empleado = getattr(user, "empleado_profile", None) if user and user.is_authenticated else None
        if empleado and not user.is_staff:
            serializer.save(empleado=empleado)
            return
        serializer.save()

