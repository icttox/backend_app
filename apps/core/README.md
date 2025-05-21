# Módulo Core

## Descripción
El módulo Core proporciona funcionalidades base y utilidades compartidas para todo el sistema APP-MANAGER. Actúa como una biblioteca central de componentes reutilizables.

## Estructura

```
core/
├── __init__.py
├── admin.py          # Configuración del panel de administración
├── apps.py          # Configuración de la aplicación
├── migrations/      # Migraciones de la base de datos
├── models.py        # Modelos de datos base
├── permissions.py   # Sistema de permisos personalizado
├── tests.py        # Pruebas unitarias
└── views.py        # Vistas base
```

## Características Principales

1. **Sistema de Permisos**
   - Permisos personalizados
   - Decoradores de permisos
   - Mixins de autorización

2. **Utilidades Base**
   - Modelos abstractos
   - Vistas genéricas
   - Funciones auxiliares

3. **Configuraciones Globales**
   - Constantes del sistema
   - Configuraciones compartidas
   - Valores por defecto

## Componentes

### Permisos
El archivo `permissions.py` contiene:
- Clases base para permisos
- Decoradores personalizados
- Validadores de permisos

### Modelos Base
Modelos abstractos que pueden ser heredados por otras aplicaciones:
- Timestamps
- Auditoría
- Metadatos comunes

### Vistas Base
Vistas genéricas que pueden ser extendidas:
- Manejo de errores
- Respuestas estándar
- Mixins comunes

## Uso

### Permisos Personalizados
```python
from apps.core.permissions import IsOwnerOrAdmin

class MyView(APIView):
    permission_classes = [IsOwnerOrAdmin]
```

### Modelos Base
```python
from apps.core.models import TimeStampedModel

class MyModel(TimeStampedModel):
    # Hereda created_at y updated_at
    name = models.CharField(max_length=100)
```

## Configuración
El módulo core no requiere configuraciones específicas, pero proporciona:
- Constantes del sistema
- Configuraciones por defecto
- Utilidades de configuración

## Extensión
Para extender las funcionalidades del módulo core:

1. Crear nuevos permisos:
```python
from apps.core.permissions import BasePermission

class MyCustomPermission(BasePermission):
    def has_permission(self, request, view):
        # Implementar lógica personalizada
        return True
```

2. Crear nuevos modelos base:
```python
from django.db import models
from apps.core.models import TimeStampedModel

class MyBaseModel(TimeStampedModel):
    # Agregar campos adicionales
    description = models.TextField()
    
    class Meta:
        abstract = True
```

## Buenas Prácticas
1. Mantener el código del core lo más genérico posible
2. Documentar todas las utilidades y componentes
3. Escribir pruebas unitarias para cada componente
4. Seguir los principios DRY (Don't Repeat Yourself)
5. Mantener la compatibilidad hacia atrás
