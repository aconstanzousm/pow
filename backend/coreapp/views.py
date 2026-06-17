# backend/coreapp/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Empleado, Pedido, PedidoItem, Producto, CafeConfig
from .serializers import EmpleadoSerializer, PedidoSerializer, ProductoSerializer, CafeConfigSerializer


# ── Login ──
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
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

    role = 'admin' if user.is_staff else 'empleado'

    return Response({
        'success': True,
        'role': role,
        'username': user.username,
        'user_id': user.id
    }, status=status.HTTP_200_OK)


# ── Estado del café (abierto/cerrado) ──
@api_view(['GET', 'PATCH'])
@permission_classes([permissions.AllowAny])
def cafe_status_view(request):
    config = CafeConfig.get()

    if request.method == 'GET':
        return Response({'abierto': config.abierto})

    # PATCH — solo admin
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response({'error': 'Solo el admin puede cambiar el estado.'}, status=status.HTTP_403_FORBIDDEN)

    abierto = request.data.get('abierto')
    if abierto is None:
        return Response({'error': 'Campo "abierto" requerido.'}, status=status.HTTP_400_BAD_REQUEST)

    config.abierto = bool(abierto)
    config.save()
    return Response({'abierto': config.abierto})


# ── Estadísticas (solo admin) ──
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def estadisticas_view(request):
    now = timezone.now()
    inicio_hoy = now.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = inicio_hoy - timedelta(days=inicio_hoy.weekday())
    inicio_mes = inicio_hoy.replace(day=1)

    def ingresos_desde(desde):
        resultado = Pedido.objects.filter(
            created_at__gte=desde,
            estado__in=['listo', 'preparando', 'pendiente']
        ).aggregate(total=Sum('total'))
        return resultado['total'] or 0

    # Productos más y menos vendidos
    productos_vendidos = (
        PedidoItem.objects
        .values('nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')
    )

    mas_vendidos = list(productos_vendidos[:5])
    menos_vendidos = list(productos_vendidos.order_by('total_vendido')[:5])

    # Ingresos por los últimos 7 días (para gráfico)
    ingresos_por_dia = []
    for i in range(6, -1, -1):
        dia = inicio_hoy - timedelta(days=i)
        dia_siguiente = dia + timedelta(days=1)
        total_dia = Pedido.objects.filter(
            created_at__gte=dia,
            created_at__lt=dia_siguiente,
            estado__in=['listo', 'preparando', 'pendiente']
        ).aggregate(total=Sum('total'))['total'] or 0
        ingresos_por_dia.append({
            'fecha': dia.strftime('%a %d'),
            'total': total_dia,
        })

    return Response({
        'ingresos': {
            'hoy': ingresos_desde(inicio_hoy),
            'semana': ingresos_desde(inicio_semana),
            'mes': ingresos_desde(inicio_mes),
        },
        'pedidos': {
            'hoy': Pedido.objects.filter(created_at__gte=inicio_hoy).count(),
            'semana': Pedido.objects.filter(created_at__gte=inicio_semana).count(),
            'mes': Pedido.objects.filter(created_at__gte=inicio_mes).count(),
        },
        'productos': {
            'mas_vendidos': mas_vendidos,
            'menos_vendidos': menos_vendidos,
        },
        'ingresos_por_dia': ingresos_por_dia,
    })


# ── ViewSets ──
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

    def create(self, request, *args, **kwargs):
        # Bloquear si el café está cerrado
        config = CafeConfig.get()
        if not config.abierto:
            return Response(
                {'error': 'El café está cerrado. No se pueden hacer pedidos en este momento.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        user = getattr(self.request, "user", None)
        empleado = getattr(user, "empleado_profile", None) if user and user.is_authenticated else None
        if empleado and not user.is_staff:
            serializer.save(empleado=empleado)
            return
        serializer.save()


# ── Frontend Views ──
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