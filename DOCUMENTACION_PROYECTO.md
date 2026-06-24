# 📋 Documentación Completa del Proyecto - Sistema de Gestión de Café

## 📑 Tabla de Contenidos
1. [Descripción General](#descripción-general)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Backend (Django)](#backend-django)
4. [Frontend (HTML/CSS/JavaScript)](#frontend-htmlcssjavascript)
5. [Base de Datos](#base-de-datos)
6. [API REST](#api-rest)
7. [Guía de Configuración](#guía-de-configuración)

---

## 🎯 Descripción General

Este es un **Sistema Integral de Gestión para Café** que permite:
- 👥 Gestionar productos (café, bebidas, alimentos)
- 📦 Controlar inventario y stock
- 📝 Registrar y seguir pedidos
- 👤 Administrar empleados
- 💰 Procesar pagos y generar reportes
- 📊 Visualizar estadísticas del negocio

**Tecnología Principal:**
- **Backend:** Django 5.2 + Django REST Framework
- **Frontend:** HTML5, CSS3, JavaScript vanilla
- **Base de Datos:** SQLite (desarrollo)
- **Autenticación:** Django Auth (usuario/contraseña)

---

## 📁 Estructura del Proyecto

```
pow/
├── backend/                    # API REST y lógica del servidor
│   ├── config/                 # Configuraciones principales de Django
│   ├── coreapp/                # Aplicación principal
│   │   ├── models.py           # Modelos de datos
│   │   ├── views.py            # Lógica de negocio y vistas
│   │   ├── serializers.py      # Conversión de datos a JSON
│   │   ├── urls.py             # Rutas de la API
│   │   ├── admin.py            # Panel administrativo Django
│   │   └── migrations/         # Cambios en la base de datos
│   ├── manage.py               # Herramienta de gestión Django
│   ├── requirements.txt        # Dependencias Python
│   ├── db.sqlite3              # Base de datos SQLite
│   └── media/                  # Imágenes de productos
│
├── frontend/                   # Interfaz de usuario
│   ├── index.html              # Página principal
│   ├── menu.html               # Menú de productos
│   ├── checkout.html           # Carrito de compras
│   ├── payment.html            # Procesamiento de pagos
│   ├── aboutus.html            # Acerca de nosotros
│   ├── index.css               # Estilos principales
│   ├── menu.css                # Estilos del menú
│   ├── test.html               # Página de pruebas
│   └── admin/                  # Panel administrativo
│       ├── admin-login.html    # Login de administrador
│       ├── admin-panel.html    # Panel de admin
│       ├── empleado-panel.html # Panel de empleado
│       └── admin.css           # Estilos administrativos
│
└── wenv/                       # Entorno virtual Python
    └── (paquetes instalados)
```

---

## 🖥️ Backend (Django)

### 📦 Modelos de Datos

#### 1. **Empleado** (`models.py`)
Representa a los trabajadores del café.

```python
- nombre: Nombre del empleado
- apellido: Apellido
- email: Email único
- telefono: Número de contacto (opcional)
- activo: Si trabaja actualmente (true/false)
- user: Vinculación con usuario de autenticación
- created_at: Fecha de creación
- updated_at: Última modificación
```

**Uso:** Gestionar personal, autenticación, y atribución de pedidos a empleados.

#### 2. **Producto** (`models.py`)
Artículos disponibles en el menú.

```python
- nombre: Nombre del producto (café, jugo, etc.)
- descripcion: Breve descripción
- precio: Costo en pesos (entero)
- categoria: Categoría (café, bebida, alimento)
- activo: Si está disponible para venta
- imagen: Foto del producto
- stock: Cantidad disponible
- stock_minimo: Cantidad mínima antes de alerta
- created_at: Fecha de creación
- updated_at: Última modificación
```

**Uso:** Catálogo de productos que los clientes pueden comprar.

#### 3. **Pedido** (`models.py`)
Registro de compras de clientes.

```python
- cliente_nombre: Nombre de quién compra
- cliente_email: Email del cliente (opcional)
- nota: Notas especiales o comentarios
- estado: PENDIENTE → PREPARANDO → LISTO → CANCELADO
- total: Monto total en pesos
- empleado: Quién prepara el pedido (opcional)
- created_at: Hora de creación
- updated_at: Última modificación
```

**Estados:**
- 🔵 **PENDIENTE:** Acababa de crearse, esperando preparación
- 🟡 **PREPARANDO:** Alguien está haciendo el pedido
- 🟢 **LISTO:** Completado, esperando retiro
- ❌ **CANCELADO:** Cancelado por el cliente

#### 4. **PedidoItem** (`models.py`)
Productos individuales dentro de un pedido.

```python
- pedido: Referencia al pedido principal
- producto: Referencia al producto
- nombre: Nombre del producto (copia en caso de cambios)
- precio: Precio en ese momento
- cantidad: Cuántas unidades
```

**Uso:** Permite múltiples productos por pedido. Ejemplo: 1 café + 2 medialunas.

#### 5. **CafeConfig** (`models.py`)
Configuración global del café (singleton).

```python
- abierto: Si el café está abierto o cerrado
- updated_at: Última vez que cambió
```

**Uso Especial:** Solo hay UN registro (pk=1). Permite abrir/cerrar el café globalmente.

---

### 🔌 Vistas API (views.py)

#### **Login** → `POST /login/`
```json
Entrada: {"username": "admin", "password": "1234"}
Salida:  {"success": true, "role": "admin", "username": "admin", "user_id": 1}
```
- Autentica usuarios
- Retorna rol (admin o empleado)

#### **Estado del Café** → `GET/PATCH /cafe-status/`
```json
GET:   {"abierto": true}
PATCH: {"abierto": false}  ← Solo admin
```

#### **Estadísticas** → `GET /estadisticas/`
- ✅ Solo admin puede acceder
- 📊 Ingresos por: día, semana, mes
- 🏆 Top 5 productos más vendidos
- 📉 Top 5 productos menos vendidos
- 📈 Gráfico con ingresos últimos 7 días

#### **ViewSets REST** (CRUD automático)

**Empleados** → `/empleados/`
- `GET /empleados/` - Listar todos
- `POST /empleados/` - Crear nuevo
- `GET /empleados/{id}/` - Obtener detalles
- `PATCH /empleados/{id}/` - Modificar
- `DELETE /empleados/{id}/` - Eliminar

**Productos** → `/productos/`
- `GET /productos/` - Listar menú
- `POST /productos/` - Crear producto
- `GET /productos/{id}/` - Detalles
- `PATCH /productos/{id}/` - Editar
- `DELETE /productos/{id}/` - Eliminar

**Pedidos** → `/pedidos/`
- `GET /pedidos/` - Historial
- `POST /pedidos/` - Crear pedido
- `GET /pedidos/{id}/` - Ver detalles
- `PATCH /pedidos/{id}/` - Cambiar estado
- `DELETE /pedidos/{id}/` - Cancelar

---

### 🔄 Serializers (serializers.py)

Los serializadores convierten modelos Python a JSON y viceversa.

#### **EmpleadoSerializer**
- Convierte datos de empleado a JSON
- Maneja creación de usuario
- Encripta contraseña automáticamente

#### **ProductoSerializer**
- Incluye URL de imagen
- Campo `bajo_stock`: True si stock ≤ stock_minimo

#### **PedidoSerializer & PedidoItemSerializer**
- Maneja la relación compleja pedido-items
- Valida cantidad y precio

---

## 🎨 Frontend (HTML/CSS/JavaScript)

### 📄 Páginas Principales

#### **1. `index.html` - Inicio**
- Logo y bienvenida del café
- Botón para acceder al menú
- Información general

#### **2. `menu.html` - Menú de Productos**
- 📋 Lista de productos con:
  - Foto del producto
  - Nombre y descripción
  - Precio
  - Botón "Agregar al carrito"
- 🛒 Carrito flotante que muestra:
  - Cantidad de items
  - Total a pagar
  - Botones: Vaciar carrito, Ir a checkout

#### **3. `checkout.html` - Carrito de Compras**
- 📦 Resumen de items agregados
- Cantidad y precio individual
- Total de la compra
- Campos de cliente:
  - Nombre
  - Email (opcional)
  - Notas especiales
- Botón "Proceder al pago"

#### **4. `payment.html` - Procesamiento de Pago**
- 💳 Método de pago
- Confirmación de datos
- Finalización de compra
- Generación de recibo

#### **5. `aboutus.html` - Acerca de Nosotros**
- 📖 Historia del café
- Equipo
- Contacto
- Ubicación

#### **6. `test.html` - Página de Pruebas**
- Para desarrollo y debugging
- Pruebas de API

---

### 👥 Panel Administrativo (`admin/`)

#### **1. `admin-login.html`**
- 🔐 Login solo para administradores
- Usuario y contraseña
- Verificación de permisos (is_staff)

#### **2. `admin-panel.html`**
- 📊 Dashboard con estadísticas
- Gestión de:
  - Productos (CRUD)
  - Empleados (CRUD)
  - Pedidos (ver estado)
- 📈 Gráficos de ventas
- 💰 Ingresos totales

#### **3. `empleado-panel.html`**
- 👤 Panel para empleados
- Ver pedidos asignados
- Cambiar estado de pedidos
  - Pendiente → Preparando → Listo
- Ver productos en inventario
- Alertas de bajo stock

---

### 🎯 Flujo de Usuario Cliente

```
1. Entra a index.html
   ↓
2. Va a menu.html
   ↓
3. Selecciona productos → se agregan al carrito
   ↓
4. Va a checkout.html
   ↓
5. Ingresa nombre y email
   ↓
6. Procede a payment.html
   ↓
7. Completa pago
   ↓
8. ✅ Pedido creado (estado: PENDIENTE)
```

---

### 🎯 Flujo de Usuario Empleado

```
1. Accede a admin/empleado-panel.html
   ↓
2. Se autentica (login)
   ↓
3. Ve pedidos en estado PENDIENTE
   ↓
4. Cambia a PREPARANDO (comienza a hacer)
   ↓
5. Cambia a LISTO (termina)
   ↓
6. Cliente retira → Pedido completado
```

---

### 🎯 Flujo de Usuario Admin

```
1. Accede a admin/admin-login.html
   ↓
2. Se autentica (solo si es_admin/is_staff)
   ↓
3. En admin-panel.html puede:
   ├─ Ver estadísticas y gráficos
   ├─ Agregar/editar productos
   ├─ Crear/eliminar empleados
   ├─ Ver todos los pedidos
   ├─ Abrir/cerrar el café
   └─ Descargar reportes
```

---

## 💾 Base de Datos

### Estructura SQLite (`db.sqlite3`)

```sql
EMPLEADO
├─ id (PK)
├─ nombre
├─ apellido
├─ email (UNIQUE)
├─ telefono
├─ activo (DEFAULT: true)
├─ user_id (FK → Django User)
└─ timestamps

PRODUCTO
├─ id (PK)
├─ nombre
├─ descripcion
├─ precio
├─ categoria
├─ activo (DEFAULT: true)
├─ imagen (archivo)
├─ stock
├─ stock_minimo (DEFAULT: 5)
└─ timestamps

PEDIDO
├─ id (PK)
├─ cliente_nombre
├─ cliente_email
├─ nota
├─ estado (ENUM: pendiente/preparando/listo/cancelado)
├─ total
├─ empleado_id (FK → Empleado, NULL)
└─ timestamps

PEDIDO_ITEM
├─ id (PK)
├─ pedido_id (FK → Pedido)
├─ producto_id (FK → Producto)
├─ nombre (snapshot)
├─ precio (snapshot)
└─ cantidad

CAFE_CONFIG
├─ id = 1 (Singleton)
├─ abierto (boolean)
└─ updated_at
```

### Migraciones
- `0001_initial.py` - Creación inicial
- `0002_producto_imagen.py` - Agregó campo imagen
- `0003_cafeconfig.py` - Agregó tabla de configuración
- `0004_producto_stock.py` - Agregó stock
- `0005_producto_stock_minimo_alter_producto_stock.py` - Stock mínimo

---

## 🌐 API REST

### Base URL
```
http://localhost:8000/api/
```

### Endpoints Principales

#### **Autenticación**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/login/` | Autenticar usuario |
| GET/PATCH | `/cafe-status/` | Ver/cambiar estado café |
| GET | `/estadisticas/` | Ver estadísticas (solo admin) |

#### **Productos**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/productos/` | Listar todos |
| POST | `/productos/` | Crear nuevo |
| GET | `/productos/{id}/` | Ver detalles |
| PATCH | `/productos/{id}/` | Editar |
| DELETE | `/productos/{id}/` | Eliminar |

#### **Pedidos**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/pedidos/` | Listar todos |
| POST | `/pedidos/` | Crear nuevo |
| GET | `/pedidos/{id}/` | Ver detalles |
| PATCH | `/pedidos/{id}/` | Cambiar estado |
| DELETE | `/pedidos/{id}/` | Cancelar |

#### **Empleados**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/empleados/` | Listar todos |
| POST | `/empleados/` | Crear nuevo |
| GET | `/empleados/{id}/` | Ver detalles |
| PATCH | `/empleados/{id}/` | Editar |
| DELETE | `/empleados/{id}/` | Eliminar |

### Ejemplo de Requests

**Crear Pedido:**
```bash
POST /pedidos/
{
  "cliente_nombre": "Juan Pérez",
  "cliente_email": "juan@email.com",
  "nota": "Café sin azúcar",
  "items": [
    {"producto_id": 1, "cantidad": 2},
    {"producto_id": 3, "cantidad": 1}
  ]
}
```

**Cambiar estado de pedido:**
```bash
PATCH /pedidos/5/
{
  "estado": "preparando"
}
```

---

## ⚙️ Guía de Configuración

### 📋 Requisitos
- Python 3.10+
- pip (gestor de paquetes)
- Navegador web moderno

### 🚀 Instalación

**1. Crear entorno virtual:**
```bash
python -m venv wenv
```

**2. Activar entorno:**
```bash
# Windows
wenv\Scripts\activate

# Mac/Linux
source wenv/bin/activate
```

**3. Instalar dependencias:**
```bash
pip install -r backend/requirements.txt
```

### ▶️ Ejecución

**1. Aplicar migraciones:**
```bash
cd backend
python manage.py migrate
```

**2. Crear superusuario (admin):**
```bash
python manage.py createsuperuser
# username: admin
# password: (ingresa contraseña)
```

**3. Iniciar servidor:**
```bash
python manage.py runserver
```

**4. Acceder:**
- Frontend: http://localhost:8000/
- Admin Django: http://localhost:8000/admin/

### 📁 Estructura de Carpetas Importante

```
backend/
├── config/
│   ├── settings.py ← Configuración Django
│   ├── urls.py ← Rutas principales
│   └── cors.py ← Configuración CORS
├── coreapp/
│   ├── models.py ← Definición de datos
│   ├── views.py ← Lógica de negocio
│   ├── serializers.py ← Conversión a JSON
│   └── urls.py ← Rutas de API
└── media/
    └── productos/ ← Imágenes de productos

frontend/
├── index.html ← Inicio
├── menu.html ← Menú
├── checkout.html ← Carrito
├── payment.html ← Pago
└── admin/
    ├── admin-login.html
    ├── admin-panel.html
    └── empleado-panel.html
```

---

## 🔐 Seguridad

- ✅ Contraseñas encriptadas con Django (PBKDF2)
- ✅ Autenticación por usuario/contraseña
- ✅ Roles: Admin (is_staff) y Empleado (staff=false)
- ✅ CORS habilitado en config/cors.py
- ✅ Endpoints protegidos con permisos

---

## 📊 Caso de Uso Completo

### Escenario: Cliente compra café

```
1. Cliente entra a index.html
2. Navega a menu.html
3. Ve café ($3.500), medialuna ($2.000), jugo ($2.500)
4. Agrega: 2 cafés + 1 medialuna al carrito
   Total: 9.000
5. Va a checkout.html
6. Ingresa: "Carlos López", "carlos@email.com"
7. Procede a payment.html
8. Confirma pago → se crea PEDIDO #42
9. Estado: PENDIENTE

→ Un empleado lo ve en su panel
→ Cambia a PREPARANDO
→ Prepara: 2 cafés + 1 medialuna
→ Cambia a LISTO
→ Cliente retira
→ Pedido completado ✅
```

### Escenario: Admin gestiona inventario

```
1. Admin entra a admin-panel.html
2. Ve que café tiene stock bajo (2 unidades)
   - Alerta de bajo stock (mínimo: 5)
3. Va a "Gestionar productos"
4. Edita café:
   - Stock actual: 2
   - Nuevo stock: 25
   - Guarda
5. Sistema actualiza automáticamente
6. En dashboard ve que vendió 150 cafés esta semana
7. Ingresos: $525.000 esta semana
```

---

## 🛠️ Mantenimiento

### Respaldos
```bash
# Hacer backup de base de datos
cp backend/db.sqlite3 backup_db.sqlite3

# Hacer backup de imágenes
cp -r backend/media/ backup_media/
```

### Limpiar caché
```bash
# Borrar archivos compilados Python
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Actualizar dependencias
```bash
pip freeze > backend/requirements.txt
```

---

## 📚 Recursos Útiles

- [Documentación Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

## 📝 Notas Finales

Este proyecto es una **aplicación educativa** diseñada para aprender:
- ✅ Desarrollo fullstack
- ✅ Arquitectura de APIs REST
- ✅ Gestión de bases de datos relacional
- ✅ Autenticación y autorización
- ✅ Frontend interactivo

El código está **bien documentado** y es **fácil de extender** para agregar nuevas funcionalidades como:
- Integración de pagos real
- Sistema de reservas
- Notificaciones en tiempo real
- App móvil

---

**Última actualización:** Junio 2026  
**Versión:** 1.0.0
