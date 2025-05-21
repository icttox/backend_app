# Módulo de Cotizador

## Descripción
Este módulo maneja todo el sistema de cotizaciones y presupuestos en APP-MANAGER, permitiendo la gestión completa del proceso de cotización.

## Estructura

```
cotizador/
├── __init__.py
├── admin.py          # Configuración del panel de administración
├── apps.py          # Configuración de la aplicación
├── models.py        # Modelos de datos
├── routers.py       # Configuración de rutas de la API
├── serializers.py   # Serializadores para la API
├── tests.py         # Pruebas unitarias
├── urls.py          # Configuración de URLs
└── views.py         # Vistas y lógica de negocio
```

## Características Principales

1. **Gestión de Cotizaciones**
   - Creación de cotizaciones
   - Seguimiento de estado
   - Historial de cambios
   - Cálculos automáticos

2. **Productos y Servicios**
   - Catálogo de productos
   - Precios y descuentos
   - Gestión de inventario
   - Categorización

3. **Clientes**
   - Base de datos de clientes
   - Historial de cotizaciones por cliente
   - Información de contacto

## Endpoints API

### Cotizaciones
- `GET /api/cotizador/cotizaciones/` - Listar cotizaciones
- `POST /api/cotizador/cotizaciones/` - Crear cotización
- `GET /api/cotizador/cotizaciones/{id}/` - Detalle de cotización
- `PUT /api/cotizador/cotizaciones/{id}/` - Actualizar cotización
- `DELETE /api/cotizador/cotizaciones/{id}/` - Eliminar cotización

### Productos
- `GET /api/cotizador/productos/` - Listar productos
- `POST /api/cotizador/productos/` - Crear producto
- `GET /api/cotizador/productos/{id}/` - Detalle de producto

## Modelos

### Cotizacion
- Cliente
- Fecha
- Estado
- Items
- Total
- Observaciones

### Producto
- Nombre
- Descripción
- Precio
- Categoría
- Stock

### Cliente
- Información de contacto
- Historial de cotizaciones
- Preferencias

## Funcionalidades

1. **Cálculos Automáticos**
   - Subtotales
   - Impuestos
   - Descuentos
   - Total final

2. **Gestión de Estados**
   - Pendiente
   - En revisión
   - Aprobada
   - Rechazada
   - Finalizada

3. **Reportes**
   - Cotizaciones por período
   - Productos más cotizados
   - Estadísticas de conversión

## Uso

```python
# Ejemplo de creación de cotización
from apps.cotizador.models import Cotizacion, Item

def crear_cotizacion(cliente, items):
    cotizacion = Cotizacion.objects.create(
        cliente=cliente,
        estado='pendiente'
    )
    for item in items:
        Item.objects.create(
            cotizacion=cotizacion,
            producto=item['producto'],
            cantidad=item['cantidad']
        )
    return cotizacion
```

## Configuración
El módulo utiliza las siguientes configuraciones:
- Configuraciones de impuestos
- Estados de cotización
- Políticas de descuentos
- Formatos de numeración
