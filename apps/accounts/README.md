# Módulo de Accounts

## Descripción
Este módulo maneja toda la gestión de usuarios, autenticación y autorización en el sistema APP-MANAGER.

## Estructura

```
accounts/
├── __init__.py
├── admin.py          # Configuración del panel de administración
├── apps.py          # Configuración de la aplicación
├── models.py        # Modelos de datos
├── serializers.py   # Serializadores para la API
├── tests.py        # Pruebas unitarias
├── urls.py         # Configuración de URLs
└── views.py        # Vistas y lógica de negocio
```

## Características Principales

1. **Gestión de Usuarios**
   - Registro de usuarios
   - Actualización de perfiles
   - Gestión de roles y permisos

2. **Autenticación**
   - Login/Logout
   - Autenticación basada en JWT
   - Renovación de tokens
   - Blacklist de tokens

3. **Autorización**
   - Control de acceso basado en roles
   - Permisos granulares
   - Grupos de usuarios

## Endpoints API

### Autenticación
- `POST /api/accounts/login/` - Iniciar sesión
- `POST /api/accounts/logout/` - Cerrar sesión
- `POST /api/accounts/token/refresh/` - Refrescar token JWT

### Gestión de Usuarios
- `POST /api/accounts/register/` - Registrar nuevo usuario
- `GET /api/accounts/profile/` - Obtener perfil de usuario
- `PUT /api/accounts/profile/update/` - Actualizar perfil
- `POST /api/accounts/password/change/` - Cambiar contraseña

## Modelos

### User
Extensión del modelo User de Django con campos adicionales:
- Información personal
- Configuraciones específicas
- Roles y permisos personalizados

## Seguridad
- Implementación de JWT para tokens seguros
- Validación robusta de contraseñas
- Protección contra ataques comunes
- Manejo seguro de sesiones

## Uso

```python
# Ejemplo de autenticación
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
```

## Configuración
El módulo utiliza las siguientes configuraciones en settings.py:
- JWT settings
- Configuraciones de autenticación
- Validadores de contraseña
- Configuraciones de sesión
