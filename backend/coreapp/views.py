# backend/coreapp/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Empleado, Pedido, PedidoItem, Producto, CafeConfig, Cliente
from .serializers import EmpleadoSerializer, PedidoSerializer, ProductoSerializer, ClienteSerializer


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

def _vincular_pedidos_invitado(cliente):
    """Asocia al cliente todos los pedidos de invitado con el mismo email."""
    Pedido.objects.filter(cliente__isnull=True, cliente_email__iexact=cliente.email).update(cliente=cliente)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cliente_registro_view(request):
    serializer = ClienteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cliente = serializer.save()
    _vincular_pedidos_invitado(cliente)
    return Response(
        {'success': True, 'cliente': ClienteSerializer(cliente).data},
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cliente_login_view(request):
    username = (request.data.get('username') or '').strip()
    password = (request.data.get('password') or '').strip()

    if not username or not password:
        return Response({'success': False, 'error': 'Usuario y contraseña son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'success': False, 'error': 'Usuario o contraseña incorrectos.'}, status=status.HTTP_401_UNAUTHORIZED)

    cliente = getattr(user, 'cliente_profile', None)
    if not cliente:
        return Response({'success': False, 'error': 'Esta cuenta no corresponde a un cliente.'}, status=status.HTTP_403_FORBIDDEN)

    _vincular_pedidos_invitado(cliente)
    return Response({'success': True, 'cliente': ClienteSerializer(cliente).data})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def mis_pedidos_view(request):
    session_key = (request.headers.get('X-Session-Key') or '').strip()
    limite_temporal = timezone.now() - timedelta(hours=12)

    user = request.user
    cliente = getattr(user, 'cliente_profile', None) if user and user.is_authenticated else None

    if not cliente and not session_key:
        return Response({'error': 'Se requiere sesión iniciada o clave de sesión temporal.'}, status=status.HTTP_400_BAD_REQUEST)

    if cliente:
        qs = Pedido.objects.filter(
            models.Q(cliente=cliente) |
            models.Q(session_key=session_key, cliente__isnull=True, created_at__gte=limite_temporal)
        )
    else:
        qs = Pedido.objects.filter(session_key=session_key, created_at__gte=limite_temporal)

    qs = qs.prefetch_related('items').order_by('-created_at').distinct()
    return Response(PedidoSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recibo_pedido_view(request, codigo):
    pedido = Pedido.objects.prefetch_related('items').filter(codigo_pedido=codigo).first()
    if not pedido:
        return Response({'error': 'Pedido no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    session_key = (request.headers.get('X-Session-Key') or '').strip()
    user = request.user
    autorizado = False

    if user and user.is_authenticated:
        if user.is_staff or getattr(user, 'empleado_profile', None):
            autorizado = True
        cliente = getattr(user, 'cliente_profile', None)
        if cliente and pedido.cliente_id == cliente.id:
            autorizado = True

    if not autorizado and session_key and pedido.session_key == session_key:
        if pedido.created_at >= timezone.now() - timedelta(hours=12):
            autorizado = True

    if not autorizado:
        return Response({'error': 'No tienes acceso a este recibo.'}, status=status.HTTP_403_FORBIDDEN)

    return Response(PedidoSerializer(pedido).data)

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

    if isinstance(abierto, bool):
        abierto_bool = abierto
    elif isinstance(abierto, str):
        value = abierto.strip().lower()
        if value in {"true", "1", "si", "sí", "on"}:
            abierto_bool = True
        elif value in {"false", "0", "no", "off"}:
            abierto_bool = False
        else:
            return Response({'error': 'El campo "abierto" debe ser booleano.'}, status=status.HTTP_400_BAD_REQUEST)
    elif isinstance(abierto, (int, float)):
        abierto_bool = bool(abierto)
    else:
        return Response({'error': 'El campo "abierto" debe ser booleano.'}, status=status.HTTP_400_BAD_REQUEST)

    config.abierto = abierto_bool
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
        if self.action == 'ajustar_stock':
            # Admin y empleados autenticados pueden ajustar stock
            return [permissions.IsAuthenticated()]
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

    @action(detail=True, methods=['post'], url_path='ajustar-stock')
    def ajustar_stock(self, request, pk=None):
        """Suma o resta stock manualmente. Body: {"delta": 5} o {"delta": -2}"""
        producto = self.get_object()
        try:
            delta = int(request.data.get('delta', 0))
        except (TypeError, ValueError):
            return Response({'error': 'El valor de "delta" debe ser un número entero.'}, status=status.HTTP_400_BAD_REQUEST)

        if delta == 0:
            return Response({'error': 'El ajuste no puede ser 0.'}, status=status.HTTP_400_BAD_REQUEST)

        nuevo_stock = producto.stock + delta
        if nuevo_stock < 0:
            return Response({'error': 'No hay suficiente stock para esa operación.'}, status=status.HTTP_400_BAD_REQUEST)

        producto.stock = nuevo_stock
        producto.save(update_fields=['stock'])
        return Response(self.get_serializer(producto).data)


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

    def perform_create(self, serializer):
        session_key = (self.request.headers.get('X-Session-Key') or '').strip() or None
        extra = {'session_key': session_key}
        user = self.request.user
        if user and user.is_authenticated:
            cliente = getattr(user, 'cliente_profile', None)
            if cliente:
                extra['cliente'] = cliente
        serializer.save(**extra)

    def update(self, request, *args, **kwargs):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_staff:
            allowed_fields = {"estado"}
            received_fields = set(request.data.keys())
            if not received_fields or not received_fields.issubset(allowed_fields):
                return Response(
                    {'error': 'Los empleados solo pueden cambiar el estado del pedido.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            nuevo_estado = request.data.get("estado")
            if nuevo_estado not in {Pedido.Estado.PREPARANDO, Pedido.Estado.LISTO}:
                return Response(
                    {'error': 'Los empleados solo pueden marcar pedidos como preparando o listo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return super().update(request, *args, **kwargs)


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

class LoginClienteView(TemplateView):
    template_name = "login-cliente.html"

class MisPedidosView(TemplateView):
    template_name = "mis-pedidos.html"

class ReciboView(TemplateView):
    template_name = "recibo.html"