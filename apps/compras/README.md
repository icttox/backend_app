# Módulo de Compras

Esta aplicación gestiona el proceso de propuestas de compra basado en el pronóstico de existencias, con asignación de categorías específicas a cada comprador.

## Integración con APIs Externas Completa ✅

La aplicación se integra con tres APIs externas principales para su funcionamiento:

1. **API de Almacenes** ✅
   - URL: `https://api2.ercules.mx/api/v1/common/location_classifications?user_id=2&classification=0&names=0`
   - Endpoint implementado: `GET /api/v1/compras/almacenes/`
   - Descripción: Consulta directa a la API externa, sin almacenamiento local. Cada solicitud obtiene datos en tiempo real.

2. **API de Categorías de Productos** ✅
   - URL: `https://api2.ercules.mx/api/v1/common/product_classifications?user_id=2&classification=0&names=0`
   - Endpoint implementado: `GET /api/v1/compras/categorias-productos/`
   - Descripción: Obtiene las categorías de productos y las filtra automáticamente según los permisos del usuario autenticado.

3. **API de Pronóstico de Existencias** ✅
   - URL: `https://api2.ercules.mx/api/v1/stock/stock_forecasting?user_id=2&categ_ids=...&warehouse_ids=...`
   - Endpoint implementado: `GET /api/v1/compras/pronostico-existencias/`
   - Descripción: Obtiene el pronóstico de existencias filtrando por almacenes y categorías.

## Estructura Completa

La aplicación consta de los siguientes modelos principales:

1. **Categoria**: Gestiona las categorías de productos disponibles para compras. Se asignan directamente a los perfiles de usuario para determinar qué productos puede gestionar cada comprador.

2. **Almacen**: Modelo proxy para consultar los almacenes directamente desde la API externa de Odoo. No se almacenan datos localmente, sino que se consulta directamente la API externa cada vez.

3. **PropuestaCompra**: Representa el documento principal de una solicitud de compra. Contiene la información general como el comprador solicitante, estado (borrador, enviada, aprobada, rechazada), fechas, y a qué almacenes está destinada la propuesta.

4. **ItemPropuestaCompra**: Representa cada producto individual dentro de una propuesta de compra. Cada item contiene información detallada sobre un producto específico que se está solicitando, incluyendo categoría, código, nombre, cantidades y proveedor sugerido.

Las categorías de productos se asignan directamente a los perfiles de usuario (UserProfile) mediante un campo ManyToMany, lo que centraliza y simplifica la gestión de permisos.

## Configuración inicial

Para configurar la aplicación, sigue estos pasos:

1. Ejecuta las migraciones:

```bash
python manage.py makemigrations compras
python manage.py migrate compras
```

Esto creará las tablas necesarias y cargará los datos iniciales de las categorías asignadas a cada comprador.

2. Configura los usuarios de compras:

```bash
python manage.py setup_compras_users --create
```

Este comando creará los usuarios para los compradores si no existen y actualizará sus perfiles con la información de comprador.

3. Si estás migrando desde una versión anterior, puedes asignar categorías a los perfiles de usuario:

```bash
python manage.py migrate_categorias_to_profiles
```

Puedes ejecutarlo con la opción `--dry-run` para ver qué cambios haría sin aplicarlos.

4. (Opcional) Verifica la conectividad con la API de almacenes:

Puedes hacer una petición GET a `/api/v1/compras/almacenes/` para confirmar que la conexión con la API externa está funcionando correctamente.

## API Completa

### Cambios Importantes en la Estructura

A partir de la versión actual, se han realizado los siguientes cambios estructurales:

1. El modelo `LineaPropuestaCompra` ha sido renombrado a `ItemPropuestaCompra` para reflejar mejor su propósito.
2. Los endpoints relacionados han cambiado de `/api/v1/compras/lineas-propuesta/` a `/api/v1/compras/items-propuesta/`.
3. La estructura de datos de los items ha sido simplificada para enfocarse en la información esencial.

La aplicación expone los siguientes endpoints:

### Categorías y Compradores

- `GET /api/v1/compras/categorias/` - Lista todas las categorías
- `GET /api/v1/compras/categorias/?comprador=NOMBRE` - Filtra por comprador
- `GET /api/v1/compras/compradores/` - Lista todos los compradores
- `GET /api/v1/compras/compradores/mi_perfil/` - Obtiene el perfil de comprador del usuario autenticado
- `GET /api/v1/compras/compradores/mis_categorias/` - **IMPORTANTE: NUEVA RUTA** - Obtiene las categorías del usuario autenticado
- `GET /api/v1/compras/categorias-productos/` - Obtiene categorías de productos desde la API externa (filtradas automáticamente según permisos del usuario)

### Almacenes (Consulta directa a API de Odoo)

- `GET /api/v1/compras/almacenes/` - Consulta y muestra los almacenes directamente desde la API externa de Odoo
- `GET /api/v1/compras/almacenes/{id}/` - Obtiene los detalles de un almacén específico por su ID
- `GET /api/v1/compras/almacenes/test_connection/` - Verifica la conectividad con la API externa de almacenes

### Pronóstico y Propuestas

- `GET /api/v1/compras/pronostico-existencias/?categ_ids=71,64` - Obtiene pronóstico de existencias (solo categ_ids es obligatorio, los demás parámetros son opcionales)
- `GET /api/v1/compras/propuestas/` - Lista todas las propuestas de compra
- `POST /api/v1/compras/propuestas/` - Crea una nueva propuesta de compra
- `GET /api/v1/compras/propuestas/mis_propuestas/` - Lista propuestas del comprador actual
- `POST /api/v1/compras/propuestas/{id}/enviar/` - Envía una propuesta para aprobación
- `POST /api/v1/compras/propuestas/{id}/aprobar/` - Aprueba una propuesta
- `POST /api/v1/compras/propuestas/{id}/rechazar/` - Rechaza una propuesta

### Items de Propuesta (Productos individuales solicitados)

- `GET /api/v1/compras/items-propuesta/?propuesta_id=1` - Lista todos los items de una propuesta específica
- `GET /api/v1/compras/items-propuesta/?codigo=ABC123` - Filtra items por código de producto
- `GET /api/v1/compras/items-propuesta/?categoria=Materia%20Prima` - Filtra items por categoría
- `POST /api/v1/compras/items-propuesta/` - Agrega un nuevo item a una propuesta de compra existente
- `PUT /api/v1/compras/items-propuesta/{id}/` - Actualiza completamente un item existente
- `PATCH /api/v1/compras/items-propuesta/{id}/` - Actualiza parcialmente un item existente
- `DELETE /api/v1/compras/items-propuesta/{id}/` - Elimina un item de una propuesta
- `PATCH /api/v1/compras/items-propuesta/bulk_update/` - Actualiza múltiples items en una sola operación

## Cambios Importantes para el Frontend

### 1. Cambio de Endpoints para Items de Propuesta

Todos los endpoints relacionados con las líneas de propuesta ahora utilizan la ruta `/api/v1/compras/items-propuesta/` en lugar de `/api/v1/compras/lineas-propuesta/`. Asegúrate de actualizar todas las llamadas a la API en el frontend.

### 2. Consulta de Categorías Asignadas al Usuario

Para obtener las categorías asignadas al usuario autenticado, se debe usar:

```
GET /api/v1/compras/compradores/mis_categorias/
```

**NOTA**: La URL anterior reemplaza a `/api/v1/compras/categorias/mis_categorias/` que ya no existe.

### 2. Consulta de Almacenes (Cambio en la implementación)

La API de almacenes ahora funciona como un proxy directo a la API externa de Odoo, sin almacenar datos localmente. Esto significa:

- Cada consulta obtiene datos en tiempo real
- El formato de respuesta es exactamente el mismo que devuelve la API externa
- Los almacenes ya no se almacenan en la base de datos local

### 3. Nueva Estructura de PropuestaCompra y sus Items

Al crear o actualizar una propuesta de compra, ahora se utiliza la siguiente estructura:

```json
{
  "comprador": 1,
  "comentarios": "Comentarios sobre la propuesta",
  "items": [
    {
      "categoria": "Materia Prima",
      "codigo": "ABC123",
      "producto": "Tablero MDF",
      "medida": "m2",
      "registrar": 100,
      "produccion": 50,
      "cantidad_propuesta": 150,
      "proveedor": "Proveedor XYZ",
      "meses": 3,
      "comentarios": "Comentarios sobre el item"
    }
  ]
}
```

#### Campos del Modelo ItemPropuestaCompra

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `propuesta` | ForeignKey | Relación con la propuesta de compra a la que pertenece este item |
| `categoria` | CharField | Categoría del producto |
| `codigo` | CharField | Código único del producto |
| `producto` | CharField | Nombre descriptivo del producto |
| `medida` | CharField | Unidad de medida del producto (m2, kg, unidades, etc.) |
| `registrar` | DecimalField | Cantidad ya en planta pero no registrada |
| `produccion` | DecimalField | Cantidad no en planta pero ya pedida |
| `cantidad_propuesta` | DecimalField | Cantidad que se propone comprar |
| `proveedor` | CharField | Proveedor sugerido o default |
| `meses` | DecimalField | Meses de cobertura calculados |
| `comentarios` | TextField | Comentarios adicionales sobre el item |

Esta estructura simplificada facilita la gestión de los items de propuesta y mejora la claridad de los datos.

### 4. Actualización de Items en Lote

Para actualizar múltiples items de una propuesta en una sola operación, se utiliza el endpoint de actualización en lote:

```
PATCH /api/v1/compras/items-propuesta/bulk_update/
```

Con el siguiente formato de payload:

```json
{
  "propuesta_id": 1,
  "items": [
    {
      "id": 1,
      "comentarios": "Nuevo comentario para item 1"
    },
    {
      "id": 2,
      "proveedor": "Nuevo proveedor para item 2",
      "propuesta": 200
    }
  ]
}
```

La respuesta incluirá el estado de cada actualización:

```json
{
  "propuesta_id": 1,
  "results": [
    {
      "id": 1,
      "status": "success",
      "data": { ... }
    },
    {
      "id": 2,
      "status": "success",
      "data": { ... }
    }
  ]
}
```

## Flujo de Trabajo

1. **Proceso inicial**: El comprador obtiene sus categorías asignadas usando `/api/v1/compras/compradores/mis_categorias/`

2. **Consulta de almacenes**: Obtiene la lista de almacenes disponibles directamente desde la API externa de Odoo

3. **Análisis de existencias**: Consulta el pronóstico de existencias con `/api/v1/compras/pronostico-existencias/` filtrando por categorías y almacenes

4. **Creación de propuesta con items**: Crea una propuesta de compra con sus items iniciales en un solo paso usando `POST /api/v1/compras/propuestas/`
   ```json
   {
     "comprador": 1,
     "comentarios": "Propuesta basada en análisis de existencias",
     "items": [
       {
         "categoria": "Materia Prima",
         "codigo": "ABC123",
         "producto": "Tablero MDF",
         // ... otros campos
       },
       // ... más items
     ]
   }
   ```

5. **Gestión adicional de items** (si es necesario):
   - Agrega más items a la propuesta con `POST /api/v1/compras/items-propuesta/`
   - Actualiza items individuales con `PATCH /api/v1/compras/items-propuesta/{id}/`
   - Actualiza múltiples items en una sola operación con `PATCH /api/v1/compras/items-propuesta/bulk_update/`
   - Elimina items con `DELETE /api/v1/compras/items-propuesta/{id}/`

6. **Envío para aprobación**: Envía la propuesta para aprobación con `POST /api/v1/compras/propuestas/{id}/enviar/`

7. **Aprobación o rechazo**: Un usuario con permisos puede aprobar o rechazar la propuesta

## Relación entre Propuestas y Líneas

Para entender mejor la estructura de datos:

- **PropuestaCompra**: Es el documento principal o cabecera que contiene información general de la solicitud
- **ItemPropuestaCompra**: Son los items individuales dentro de esa solicitud, cada uno representando un producto específico

Es similar a una factura (documento principal) y sus líneas de detalle (productos individuales).

## Uso

Los usuarios con área "COMPRAS" y que estén asociados a un comprador podrán acceder a las categorías que tienen asignadas y crear propuestas de compra basadas en el pronóstico de existencias.
