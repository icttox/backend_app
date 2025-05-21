# Getting Started - Backend App Manager

## Requisitos Previos

- Python 3.10 o superior
- PostgreSQL 14 o superior
- pip (gestor de paquetes de Python)
- virtualenv o venv

## Estructura del Proyecto

```
back-app-manager/
├── app_manager/         # Configuración principal del proyecto
├── apps/               # Aplicaciones del sistema
├── manage.py          # Script de gestión de Django
├── requirements.txt   # Dependencias del proyecto
└── .env              # Variables de entorno (crear desde ejemplo)
```

## Configuración Inicial

1. **Clonar el Repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd back-app-manager
   ```

2. **Crear y Activar Entorno Virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variables de Entorno**
   - Copiar el archivo `.env.example` a `.env`
   - Configurar las siguientes variables:
     - `DATABASE_URL`: URL de conexión a PostgreSQL
     - `SECRET_KEY`: Clave secreta de Django
     - `DEBUG`: True/False según el entorno
     - `ALLOWED_HOSTS`: Hosts permitidos
     - `CORS_ALLOWED_ORIGINS`: Orígenes permitidos para CORS

5. **Ejecutar Migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear Superusuario**
   ```bash
   python manage.py createsuperuser
   ```

7. **Iniciar el Servidor de Desarrollo**
   ```bash
   python manage.py runserver
   ```

## Puntos Clave del Sistema

### 1. Sistema de Autenticación
- Basado en email en lugar de username
- Tokens JWT para autenticación de API
- Roles y permisos específicos por área

### 2. Estructura de Permisos
- Roles predefinidos:
  - Administrador
  - Manager
  - Vendedor
  - Backoffice
  - Marketing
- Permisos por área y unidad de negocio

### 3. APIs Principales
- `/api/auth/`: Endpoints de autenticación
- `/api/users/`: Gestión de usuarios
- `/api/quotations/`: Sistema de cotizaciones
- `/api/catalog/`: Catálogos del sistema

### 4. Validaciones del Sistema
- Validación de áreas permitidas
- Validación de unidades de negocio
- Validación de razones sociales
- Validaciones específicas por módulo

## Guías de Desarrollo

### 1. Crear Nueva Aplicación
```bash
python manage.py startapp [nombre_app] apps/[nombre_app]
```

### 2. Agregar Nuevos Modelos
1. Crear modelo en `apps/[nombre_app]/models.py`
2. Registrar en `apps/[nombre_app]/admin.py`
3. Crear migraciones: `python manage.py makemigrations`
4. Aplicar migraciones: `python manage.py migrate`

### 3. Crear Nuevos Endpoints
1. Definir serializers en `apps/[nombre_app]/serializers.py`
2. Crear viewsets en `apps/[nombre_app]/views.py`
3. Registrar URLs en `apps/[nombre_app]/urls.py`

## Pruebas
```bash
python manage.py test
```

## Comandos Útiles
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic

# Shell de Django
python manage.py shell
```

## Recursos Adicionales
- [Documentación de Django](https://docs.djangoproject.com/)
- [Documentación de Django REST Framework](https://www.django-rest-framework.org/)
- [Guía de Estilo de Código Python (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
