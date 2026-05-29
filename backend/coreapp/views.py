# backend/coreapp/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth import authenticate
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Empleado, Pedido, Producto
from .serializers import EmpleadoSerializer, PedidoSerializer, ProductoSerializer


# Login Endpoint
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Handle login for admin and employees.
    Expects: { "username": "...", "password": "..." }
    Returns: { "success": true, "role": "admin" or "empleado", "username": "..." }
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    
    if not username or not password:
        return Response(
            {'success': False, 'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response(
            {'success': False, 'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Determine role
    role = 'admin' if user.is_staff else 'empleado'
    
    return Response({
        'success': True,
        'role': role,
        'username': user.username,
        'user_id': user.id
    }, status=status.HTTP_200_OK)


# ViewSets
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

    def get_permissions(self):
        # Lectura pública, escritura solo admin
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

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


# Frontend Views
class IndexView(TemplateView):
    template_name = "index.html"


class MenuView(TemplateView):
    template_name = "menu.html"


class AboutUsView(TemplateView):
    template_name = "aboutus.html"


class CheckoutView(TemplateView):
    template_name = "checkout.html"


class PaymentView(TemplateView):
    template_name = "payment.html"


class TestView(TemplateView):
    template_name = "test.html"


class AdminLoginView(TemplateView):
    template_name = "admin/admin-login.html"


class AdminPanelView(TemplateView):
    template_name = "admin/admin-panel.html"


class EmpleadoPanelView(TemplateView):
    template_name = "admin/empleado-panel.html"

