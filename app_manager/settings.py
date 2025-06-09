from pathlib import Path
from decouple import config
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# Configuración de Supabase
SUPABASE_URL = config('SUPABASE_URL')
SUPABASE_KEY = config('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY', default=None)

# OpenAI API Key
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)

# N8N Webhook URL
N8N_WEBHOOK_URL = config('N8N_WEBHOOK_URL', default=None)

SUPABASE_BUCKET_NAME = config('SUPABASE_BUCKET_NAME', default='imagenes-productos')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Desarrollo
ALLOWED_HOSTS = ['*']

# Para asegurar que las URLs de paginación se generen correctamente
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Desactivar todas las configuraciones de seguridad HTTPS
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# CORS settings para desarrollo
#CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

# Orígenes específicos permitidos (útil si desactivas CORS_ALLOW_ALL_ORIGINS)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://front-apps-managment.vercel.app",
    "https://dashboard.appsgebesa.com",
    "https://dev-dashboard.appsgebesa.com"
]

# Permitir todos los métodos
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Permitir todos los headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning',
    'access-control-allow-origin',
]

# Configuración adicional para desarrollo
CORS_EXPOSE_HEADERS = ['*']
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 horas
CORS_ALLOW_PRIVATE_NETWORK = True

# Configuración de seguridad para desarrollo
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.ngrok-free.app",
    "https://front-apps-managment.vercel.app",
    "https://dashboard.appsgebesa.com",
]

# Configuración adicional de seguridad para desarrollo
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# Configuración de URLs
APPEND_SLASH = True

# Base URL para construir URLs absolutas
BASE_URL = 'http://127.0.0.1:8000'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Application definition

INSTALLED_APPS = [
    'jazzmin',  # debe ir antes de django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',  # Agregar django_filters a INSTALLED_APPS
    # Local apps
    'apps.accounts',
    'apps.cotizador',
    'apps.cotizador.cache',  # Agregando la aplicación de caché
    'apps.compras',  # Nueva app de compras
    'apps.aip',  # Nueva app de AIP
    'apps.analytics',  # Nueva app de Analytics
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Debe ir primero
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.cotizador.middleware.query_middleware.QueryTimeMiddleware',  # Query time tracking
]

ROOT_URLCONF = 'app_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'apps' / 'cotizador' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app_manager.wsgi.application'


# Database Replication Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('SUPABASE_DB_NAME'),
        'USER': config('SUPABASE_DB_USER'),
        'PASSWORD': config('SUPABASE_DB_PASSWORD'),
        'HOST': config('SUPABASE_DB_HOST'),
        'PORT': config('SUPABASE_DB_PORT'),
        'OPTIONS': {'sslmode': 'require'}
    },
    'erp-portalgebesa-com': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('ERP_PORTALGEBESA_DB_NAME'),
        'USER': config('ERP_PORTALGEBESA_DB_USER'),
        'PASSWORD': config('ERP_PORTALGEBESA_DB_PASSWORD'),
        'HOST': config('ERP_PORTALGEBESA_DB_HOST'),
        'PORT': config('ERP_PORTALGEBESA_DB_PORT')
    },
    'analytics': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('SUPABASE_DB_NAME'),
        'USER': config('SUPABASE_DB_USER'),
        'PASSWORD': config('SUPABASE_DB_PASSWORD'),
        'HOST': config('SUPABASE_DB_HOST'),
        'PORT': config('SUPABASE_DB_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
            'options': '-c search_path=analytics,public'
        }
    }
}

MIGRATIONS_MODULES = {
    'analytics': None,
}

# Database routers
DATABASE_ROUTERS = [
    'apps.cotizador.routers.ERPRouter',
    'app_manager.routers.DatabaseRouter',
    'apps.analytics.routers.AnalyticsRouter',
]

# Auth settings
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Configuración de autenticación
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Configuración de seguridad para API REST
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    # Agregar rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',    # Límite para usuarios no autenticados
        'user': '1000/day'    # Límite para usuarios autenticados
    },
    'COERCE_DECIMAL_TO_STRING': False,  # Esto hará que los decimales se serialicen como números
}

# Configuración de seguridad para CSRF
CSRF_COOKIE_HTTPONLY = True  # No accesible vía JavaScript
CSRF_USE_SESSIONS = True     # Usar sesiones en lugar de cookies
CSRF_COOKIE_SAMESITE = 'Strict'  # Protección contra CSRF en navegadores modernos

# JWT settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',
}

# Cache time to live is 15 minutes
CACHE_TTL = 60 * 15

# Cache key prefix
CACHE_KEY_PREFIX = 'app_manager'

# Logging configuration
import os

# Ensure logs directory exists
logs_dir = os.path.join(BASE_DIR, 'logs')
try:
    os.makedirs(logs_dir, exist_ok=True)
    print(f"Logs directory checked/created at {logs_dir}")
except Exception as e:
    print(f"Warning: Could not create logs directory: {e}")

# Improved logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(logs_dir, 'django.log'),
            'formatter': 'verbose',
        },
        'query_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(logs_dir, 'query_performance.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['query_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'gunicorn.access': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'gunicorn.error': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Set up request timeouts
REQUEST_TIMEOUT = 220  # seconds

# Confirm successful file logging setup
try:
    with open(os.path.join(logs_dir, 'query_performance.log'), 'a') as f:
        print("File logging set up successfully to", os.path.join(logs_dir, 'query_performance.log'))
except Exception as e:
    print(f"Warning: Could not set up file logging: {e}")

# Configuración de Jazzmin
JAZZMIN_SETTINGS = {
    # título de la página de administración
    "site_title": "APP Manager Admin",
    # Título que aparece en la barra superior
    "site_header": "APP Manager",
    # Título en la página de inicio del administrador
    "site_brand": "APP Manager",
    # Logo para tu sitio, debe estar presente en static files
    # "site_logo": "books/img/logo.png",
    # Imagen que aparecerá en la pantalla de inicio
    "welcome_sign": "Bienvenido al Panel de Administración",
    # Copyright en el footer
    "copyright": "Manufacturas Post Form SA DE CV",
    # Lista de modelo o urls personalizadas
    "topmenu_links": [
        # Url que redirige a la página de inicio del administrador
        {"name": "Inicio", "url": "admin:index", "permissions": ["auth.view_user"]},
        # modelo externo o url personalizada
        {"model": "auth.User"},
    ],
    # Ya sea para mostrar el selector de interfaz de usuario, True/False
    "show_ui_builder": True,
    # Enlaces relacionados a mostrar
    "related_modal_active": True,
    # Personalización de colores
    "primary_color": "#2B3746",  # Color principal
    "secondary_color": "#354151",  # Color secundario
    # Personalización del tema
    "custom_css": None,
    "custom_js": None,
    # Ya sea para mostrar el botón de inicio de sesión superior derecho
    "show_sidebar": True,
    "navigation_expanded": True,
    # Íconos personalizados para modelos de administración
    "icons": {
        # Autenticación y usuarios
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "accounts": "fas fa-user-shield",
        "accounts.UserProfile": "fas fa-id-card",
        "accounts.Unidad": "fas fa-building",
        "accounts.OdooUser": "fas fa-user-tie",
        
        # Módulo de compras
        "compras": "fas fa-shopping-cart",
        "compras.Categoria": "fas fa-tags",
        "compras.Almacen": "fas fa-warehouse",
        "compras.PropuestaCompra": "fas fa-file-invoice",
        "compras.LineaPropuestaCompra": "fas fa-list",
        
        # Módulo de cotizador
        "cotizador": "fas fa-calculator",
        "cotizador.Cotizacion": "fas fa-file-invoice-dollar",
        "cotizador.Cliente": "fas fa-handshake",
        "cotizador.ProductTemplate": "fas fa-box",
        
        # Otros módulos (personalizar según sea necesario)
        "core": "fas fa-cogs",
    },
}

# UI Tweaks
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.cotizador.middleware.query_middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Odoo configuration
ODOO_ENDPOINT = os.environ.get('ODOO_ENDPOINT', 'https://erp.portalgebesa.com/send_request?model=sale.order')
