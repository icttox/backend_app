# APP-MANAGER

Sistema de gestión empresarial desarrollado con Django 5.0.1 y Django REST Framework.

## Descripción

APP-MANAGER es una aplicación web robusta diseñada para la gestión empresarial, que incluye módulos para manejo de cuentas de usuario, funcionalidades core del negocio y un sistema de cotizaciones.

## Características Principales

### Sistema de Usuarios y Permisos

#### Modelo de Usuario
- Autenticación basada en email
- Campos personalizados:
  - Información personal (nombre, apellido, teléfono)
  - Área (RH, Ventas, Compras, Producción, TI)
  - Unidad (CDMX, Querétaro, Laguna, Monterrey, SPL, Guadalajara)
  - Razón Social (GEBESA NACIONAL, OPERADORA DE SUCURSALES GEBESA, SALMON DE LA LAGUNA)
- Validaciones automáticas:
  - Correspondencia entre unidad y razón social
  - Validación de áreas permitidas
  - Restricciones por rol y unidad

#### Sistema de Permisos
- Roles definidos:
  - Administrador: Acceso total al sistema
  - Manager: Gestión de cotizaciones globales
  - Vendedor: Creación y visualización de cotizaciones propias
  - Backoffice: Edición y procesamiento de cotizaciones
  - Marketing: Gestión de contenido multimedia
- Permisos por área:
  - Ventas: Acceso al módulo de cotizaciones
  - Otras áreas: Permisos específicos por módulo
- Validaciones de unidad y razón social:
  - Restricción de acceso por unidad asignada
  - Validación de razón social correspondiente

### Módulo de Cotizaciones

#### Características
- Generación automática de folios por año (formato: COT-YYYY-XXXX)
- Validación de unidad de facturación
- Cálculo automático de precios y descuentos usando Decimal para precisión financiera
- Historial de modificaciones
- Soporte para productos y servicios
- Manejo de descuentos por producto
- Creación de bundles de productos
- Cálculo automático de subtotal, IVA y total
- Gestión de imágenes de productos
- Creación de cotizaciones en un solo paso (incluye productos)

#### Permisos Específicos
- Creación: Solo roles Manager y Vendedor del área de Ventas
- Visualización: 
  - Manager: Todas las cotizaciones del sistema
  - Vendedor: Solo sus propias cotizaciones
- Edición: Solo Backoffice, Managers y Administradores

#### API Endpoints de Cotizaciones
```
GET /api/v1/cotizador/cotizaciones/
- Listar cotizaciones
- Filtros: cliente, estado, fecha, folio
- Búsqueda: folio, cliente, proyecto, razón social, RFC
- Ordenamiento: created_at, updated_at, folio_cotizacion
- Paginación incluida

POST /api/v1/cotizador/cotizaciones/
- Crear nueva cotización
- Permite crear productos en el mismo request
- Validación automática de campos numéricos
- Cálculo automático de totales

GET /api/v1/cotizador/cotizaciones/{id}/
- Ver detalle de cotización
- Incluye productos relacionados
- Muestra cálculos actualizados

PUT /api/v1/cotizador/cotizaciones/{id}/
- Actualizar cotización completa
- Actualiza productos relacionados
- Recalcula totales automáticamente

PATCH /api/v1/cotizador/cotizaciones/{id}/
- Actualización parcial de cotización
- Solo actualiza campos enviados
- Mantiene integridad de datos

DELETE /api/v1/cotizador/cotizaciones/{id}/
- Eliminar cotización
- Solo disponible en estado borrador
- Requiere permisos especiales
```

#### Modelos de Datos
- **Cotizacion**: Datos principales de la cotización
- **DetalleCotizacion**: Productos y servicios incluidos
- **Bundle**: Agrupación de productos relacionados
- **ProductoBundle**: Productos individuales dentro de un bundle
- **CotizadorImagenproducto**: Gestión de imágenes de productos

#### Características Técnicas
- Uso de Decimal para cálculos financieros precisos
- Validaciones robustas en serializers
- Manejo transaccional para operaciones múltiples
- Optimización de consultas para mejor rendimiento
- Integración con sistema de usuarios y permisos

## API Endpoints Detallados

### Autenticación
```
POST /api/auth/login/
- Login de usuario
- Devuelve: token de acceso, información del usuario y apps permitidas
- Público

POST /api/auth/logout/
- Cierre de sesión
- Requiere: token de refresco
- Autenticado

GET /api/auth/verify/
- Verifica accesos del usuario
- Devuelve: lista de aplicaciones permitidas
- Autenticado
```

### Usuarios
```
GET /api/users/
- Listar usuarios
- Filtros: email, área, unidad
- Solo administradores

POST /api/users/
- Crear nuevo usuario
- Solo administradores

GET /api/users/{id}/
- Ver detalle de usuario
- Admins: cualquier usuario
- Usuarios: solo su propio perfil

PUT /api/users/{id}/
- Actualizar usuario
- Admins: cualquier usuario
- Usuarios: solo su propio perfil

DELETE /api/users/{id}/
- Eliminar usuario
- Solo administradores

POST /api/users/{id}/change-password/
- Cambiar contraseña
- Requiere: contraseña actual
- Usuario propio o admin

POST /api/users/{id}/activate/
- Activar cuenta
- Solo administradores

POST /api/users/{id}/deactivate/
- Desactivar cuenta
- Solo administradores

GET /api/users/check-email/
- Verificar disponibilidad de email
- Público
```

### Cotizaciones
```
GET /api/cotizaciones/
- Listar cotizaciones
- Filtros: fecha, estado, unidad
- Permisos según rol

POST /api/cotizaciones/
- Crear cotización
- Solo Manager y Vendedor
- Área de Ventas

GET /api/cotizaciones/{id}/
- Ver cotización
- Permisos según rol y unidad

PUT /api/cotizaciones/{id}/
- Actualizar cotización
- Manager: todas
- Backoffice: su unidad
- Vendedor: propias en borrador

DELETE /api/cotizaciones/{id}/
- Eliminar cotización
- Solo administradores
```

### Detalles de Cotización
```
GET /api/detalles-cotizacion/
- Listar detalles
- Filtros: cotización
- Permisos heredados de cotización

POST /api/detalles-cotizacion/
- Agregar detalle
- Permisos heredados de cotización

PUT /api/detalles-cotizacion/{id}/
- Actualizar detalle
- Permisos heredados de cotización

DELETE /api/detalles-cotizacion/{id}/
- Eliminar detalle
- Permisos heredados de cotización
```

### Productos
```
GET /api/productos/
- Listar productos
- Filtros: nombre, código
- Solo lectura
- Área de Ventas
```

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed on your system

### Configuration Files
- **Dockerfile**: Defines the application container based on Python 3.11
- **docker-compose.yml**: Orchestrates multiple services (web, celery, celery-beat, redis)
- **.dockerignore**: Excludes unnecessary files from the Docker context
- **docker-entrypoint.sh**: Startup script that handles application initialization

### Environment Variables
The application uses environment variables for configuration, which should be defined in a `.env` file in the project root. Make sure to create this file with the following variables:

```
# Django settings
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432

# Static and media files
STATIC_URL=/static/
MEDIA_URL=/media/
DJANGO_SKIP_COLLECTSTATIC=1  # Set to 0 to run collectstatic on startup
```

### Running with Docker
To start the application with Docker, run:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Volumes
The following volumes are defined in docker-compose.yml:
- **static_volume**: For Django static files
- **media_volume**: For user-uploaded media files
- **redis_data**: For Redis persistence
- **logs**: For application logs

### Troubleshooting
1. **Log files**: Application logs are stored in the `/app/logs` directory
2. **Redis warnings**: The Redis service is configured with `vm.overcommit_memory=1` to avoid memory-related warnings
3. **Static files**: If static files aren't being served correctly, try setting `DJANGO_SKIP_COLLECTSTATIC=0` to run the collectstatic command

## Tecnologías Utilizadas

- Python 3.11+
- Django 5.0.1
- Django REST Framework
- PostgreSQL
- JWT para autenticación
- Django Jazzmin para el panel de administración
- Django CORS Headers para manejo de CORS
- Pillow para procesamiento de imágenes

## Estructura del Proyecto

```
APP-MANAGER/
├── app_manager/          # Configuración principal del proyecto
├── apps/                 # Aplicaciones del proyecto
│   ├── accounts/        # Gestión de usuarios y autenticación
│   ├── core/           # Funcionalidades principales
│   └── cotizador/      # Sistema de cotizaciones
├── manage.py            # Script de gestión de Django
├── requirements.txt     # Dependencias del proyecto
└── .env                # Variables de entorno (no versionado)
```

## Requisitos del Sistema

- Python 3.11+
- PostgreSQL
- Entorno virtual (recomendado)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd APP-MANAGER
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
- Crear archivo `.env` basado en el ejemplo proporcionado
- Configurar las variables necesarias (DB, SECRET_KEY, etc.)

5. Realizar migraciones:
```bash
python manage.py migrate
```

6. Crear superusuario:
```bash
python manage.py createsuperuser
```

7. Iniciar el servidor:
```bash
python manage.py runserver
```

## Módulos Principales

### Accounts
- Gestión de usuarios con campos personalizados:
  - Unidad (CDMX, QRO, LAG, MTY, SPL, GDL)
  - Razón Social (GEBESA NACIONAL, OPERADORA DE SUCURSALES GEBESA, SALMON DE LA LAGUNA)
- Autenticación JWT
- Perfiles de usuario
- Control de permisos
- Gestión de áreas (RH, Ventas, Compras, Producción, TI)

### Core
- Funcionalidades base del sistema
- Configuraciones generales
- Utilidades compartidas
- Sistema de permisos personalizados

### Cotizador
- Sistema completo de cotizaciones
- Gestión de clientes y productos
- Integración con sistema ERP existente
- Campos principales:
  - Información del cliente (proyecto, datos de contacto)
  - Información del representante
  - Unidad de facturación vinculada a razón social
  - Estados de cotización (Borrador, Enviada, Aceptada, etc.)
  - Folio automático con formato personalizado
- Conexión con catálogos del ERP:
  - Tipos de producto
  - Familias de producto
  - Líneas de producto
  - Grupos de producto

## Pendientes
- [ ] Configurar correctamente la conexión con Supabase
- [ ] Implementar validaciones adicionales en el modelo de Cotización
- [ ] Agregar endpoints en la API REST para el módulo de cotizaciones
- [ ] Documentar la API con Swagger/OpenAPI

## Variables de Entorno Requeridas

```bash
# Django
SECRET_KEY=your-secret-key

# Database - Supabase
SUPABASE_DB_NAME=your-db-name
SUPABASE_DB_USER=your-db-user
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_DB_HOST=your-db-host
SUPABASE_DB_PORT=your-db-port

# Database - ERP
ERP_PORTALGEBESA_DB_NAME=your-erp-db-name
ERP_PORTALGEBESA_DB_USER=your-erp-db-user
ERP_PORTALGEBESA_DB_PASSWORD=your-erp-db-password
ERP_PORTALGEBESA_DB_HOST=your-erp-db-host
ERP_PORTALGEBESA_DB_PORT=your-erp-db-port
```

## Configuración

El proyecto utiliza python-decouple para la gestión de variables de entorno. Asegúrese de configurar las siguientes variables en el archivo `.env`:

- SECRET_KEY
- DEBUG
- DATABASE_URL
- ALLOWED_HOSTS
- Otras configuraciones específicas

## Seguridad

- Implementación de JWT para autenticación segura
- CORS configurado para control de acceso
- Manejo seguro de contraseñas y datos sensibles

## Contribución

1. Fork el repositorio
2. Cree una rama para su característica (`git checkout -b feature/AmazingFeature`)
3. Commit sus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abra un Pull Request

## Licencia

Este proyecto está bajo licencia privada. Todos los derechos reservados.

## Soporte

Para soporte o consultas, contacte al equipo de desarrollo.

## Sistema de Permisos y Roles

### Roles del Sistema

#### 1. Administrador
- **Nivel de Acceso**: Total
- **Capacidades**:
  - Gestión completa de usuarios
  - Acceso a todos los módulos
  - Bypass de restricciones de unidad/razón social
  - Modificación de configuraciones del sistema
  - Visualización de logs y auditoría

#### 2. Manager
- **Nivel de Acceso**: Global
- **Capacidades**:
  - Ver todas las cotizaciones del sistema
  - Crear nuevas cotizaciones
  - Aprobar/Rechazar cotizaciones
  - Ver reportes globales
- **Restricciones**:
  - Debe pertenecer al área de Ventas

#### 3. Vendedor
- **Nivel de Acceso**: Personal
- **Capacidades**:
  - Crear nuevas cotizaciones
  - Ver sus propias cotizaciones
  - Modificar cotizaciones en borrador
- **Restricciones**:
  - Solo ve sus propias cotizaciones
  - No puede aprobar cotizaciones
  - Debe pertenecer al área de Ventas

#### 4. Backoffice
- **Nivel de Acceso**: Por Unidad
- **Capacidades**:
  - Editar cotizaciones aprobadas
  - Procesar documentación
  - Generar reportes
- **Restricciones**:
  - No puede crear nuevas cotizaciones
  - Solo puede editar cotizaciones de su unidad

#### 5. Marketing
- **Nivel de Acceso**: Global con restricciones
- **Capacidades**:
  - Gestión de contenido multimedia
  - Actualización de catálogos
- **Restricciones**:
  - Sin acceso al módulo de cotizaciones
  - Sin capacidad de modificar datos sensibles

## Validaciones del Sistema

### 1. Validaciones de Usuario

#### Validaciones de Área
```python
AREAS_PERMITIDAS = [
    'RH',        # Recursos Humanos
    'VENTAS',    # Ventas
    'COMPRAS',   # Compras
    'PROD',      # Producción
    'TI'         # Tecnología
]
```
- Cada usuario debe tener un área asignada
- El área determina el acceso a módulos específicos
- Validación automática al crear/modificar usuarios

#### Validaciones de Unidad
```python
UNIDADES_NEGOCIO = [
    'CDMX',      # Ciudad de México
    'QRO',       # Querétaro
    'LAG',       # Laguna
    'MTY',       # Monterrey
    'SPL',       # San Pedro Lagunillas
    'GDL'        # Guadalajara
]
```
- Cada usuario debe pertenecer a una unidad
- La unidad determina el alcance de visibilidad
- Validación contra lista predefinida

#### Validaciones de Razón Social
```python
RAZONES_SOCIALES = [
    'GEBESA_NACIONAL',
    'OPERADORA_DE_SUCURSALES_GEBESA',
    'SALMON_DE_LA_LAGUNA'
]

# Mapeo de unidades a razones sociales permitidas
UNIDAD_RAZON_SOCIAL_MAPPING = {
    'CDMX': ['GEBESA_NACIONAL', 'OPERADORA_DE_SUCURSALES_GEBESA'],
    'QRO':  ['GEBESA_NACIONAL', 'OPERADORA_DE_SUCURSALES_GEBESA'],
    'LAG':  ['SALMON_DE_LA_LAGUNA'],
    'MTY':  ['GEBESA_NACIONAL', 'OPERADORA_DE_SUCURSALES_GEBESA'],
    'SPL':  ['GEBESA_NACIONAL'],
    'GDL':  ['GEBESA_NACIONAL', 'OPERADORA_DE_SUCURSALES_GEBESA']
}
```
- Cada unidad tiene razones sociales específicas permitidas
- Validación automática al asignar razón social
- Los superusuarios están exentos de esta validación

### 2. Validaciones de Cotizaciones

#### Permisos de Creación
```python
def can_create_cotizacion(user):
    """
    Verifica si un usuario puede crear cotizaciones:
    - Debe tener rol Manager o Vendedor
    - Su razón social debe corresponder con su unidad
    - Debe pertenecer al área de ventas
    """
```
- Solo usuarios del área de Ventas
- Rol debe ser Manager o Vendedor
- Razón social debe corresponder a su unidad

#### Permisos de Visualización
```python
def can_view_cotizaciones(user, cotizacion_owner=None):
    """
    Verifica permisos para ver cotizaciones:
    - Manager y Backoffice ven todas las cotizaciones
    - Vendedores solo ven sus propias cotizaciones
    - Debe pertenecer al área de ventas
    """
```
- Managers tienen acceso global a todas las cotizaciones
- Vendedores solo ven sus propias cotizaciones
- Validación de área de ventas requerida

#### Permisos de Edición
```python
def can_edit_cotizacion(user, cotizacion):
    """
    Verifica permisos para editar cotizaciones:
    - Administradores pueden editar todo
    - Managers pueden editar cualquier cotización
    - Backoffice solo puede editar de su unidad/razón social
    """
```
- Managers tienen permisos globales de edición
- Backoffice mantiene restricciones por unidad
- Control de estado de la cotización

## Implementación de Permisos

### 1. A Nivel de Modelo
```python
class User(AbstractUser):
    def clean(self):
        # Validar área
        if self.area not in dict(self.AREA_CHOICES):
            raise ValidationError(...)
        
        # Validar unidad y razón social
        if not self.is_superuser:
            razones_permitidas = UNIDAD_RAZON_SOCIAL_MAPPING.get(self.unidad, [])
            if self.razon_social not in razones_permitidas:
                raise ValidationError(...)
```

### 2. A Nivel de Vista
```python
class CotizadorPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Validar autenticación
        if not request.user.is_authenticated:
            return False
            
        # Validar rol
        role = get_cotizador_rol(request.user)
        if not role:
            return False

        # Validar permisos específicos
        if request.method == 'POST':
            return can_create_cotizacion(request.user)
        
        return can_view_cotizaciones(request.user)
```

### 3. A Nivel de Admin
```python
class CustomUserAdmin(UserAdmin):
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo usuario
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
```

## Notas Importantes

1. **Jerarquía de Permisos**
   - Los permisos se validan en cascada
   - Primero se valida el área
   - Luego la unidad
   - Finalmente la razón social

2. **Excepciones**
   - Los superusuarios bypasan todas las validaciones
   - Algunos roles tienen permisos especiales en sus áreas

3. **Auditoría**
   - Todas las acciones son registradas
   - Se mantiene historial de cambios
   - Trazabilidad completa de modificaciones

4. **Seguridad**
   - Validaciones tanto en frontend como backend
   - Tokens JWT para autenticación
   - Sesiones con tiempo de expiración

## Base de Datos

### Tablas en PostgreSQL (ERP)
- users
- cotizaciones
- detalles_cotizacion
- productos
- ...

### Tablas en Supabase
```sql
-- Tabla para almacenar imágenes FALTA DE AGREGAR (PENDIENTE SERGIO)
CREATE TABLE imagenes (
    id SERIAL PRIMARY KEY,
    clave_padre VARCHAR(50) NOT NULL,    -- ID de referencia al registro en PostgreSQL
    tipo_registro VARCHAR(30) NOT NULL,   -- 'cotizacion', 'producto', etc.
    url TEXT NOT NULL,                    -- URL de la imagen en Supabase Storage
    nombre_archivo VARCHAR(255) NOT NULL,
    tipo_archivo VARCHAR(50) NOT NULL,    -- MIME type
    tamanio INTEGER NOT NULL,             -- Tamaño en bytes
    orden INTEGER DEFAULT 0,              -- Para ordenar múltiples imágenes
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_imagen UNIQUE (clave_padre, tipo_registro, nombre_archivo)
);

-- Índices
CREATE INDEX idx_imagenes_clave_padre ON imagenes(clave_padre);
CREATE INDEX idx_imagenes_tipo_registro ON imagenes(tipo_registro);
```

### Relación con PostgreSQL
- Las imágenes se almacenan físicamente en Supabase Storage
- La tabla `imagenes` mantiene la relación entre los registros de PostgreSQL y sus imágenes
- La `clave_padre` se relaciona con el ID del registro correspondiente en PostgreSQL
- Ejemplo de relación:
  ```
  PostgreSQL: cotizacion.id = 1234
  Supabase: imagenes.clave_padre = '1234' AND tipo_registro = 'cotizacion'
  ```

## Dependencias Actualizadas
```
asgiref==3.8.1
Django==5.0.1
django-cors-headers==4.3.1
django-filter==23.5
django-jazzmin==3.0.1
djangorestframework==3.14.0
djangorestframework_simplejwt==5.4.0
pillow==11.1.0
psycopg2-binary==2.9.9
PyJWT==2.10.1
python-decouple==3.8
pytz==2025.1
sqlparse==0.5.3
tzdata==2025.1
