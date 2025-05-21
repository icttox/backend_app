from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
import requests
from django.db.models import Q
from django.conf import settings
from urllib.parse import urlencode
from .models import ProductsCache
from .serializers import ProductsCacheSerializer, ProductImageUploadSerializer
from apps.cotizador.models import CotizadorImagenproducto
from apps.cotizador.utils.upload_helpers import upload_image_to_supabase
from supabase import create_client, Client

class CustomPagination(PageNumberPagination):
    """
    Paginación personalizada que permite al cliente especificar el tamaño de página
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'total': self.page.paginator.count,
            'page_size': self.get_page_size(self.request),
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

    def get_next_link(self):
        if not self.page.has_next():
            return None
        
        url = self.request.build_absolute_uri()
        page_number = self.page.next_page_number()
        
        return self._replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        
        url = self.request.build_absolute_uri()
        page_number = self.page.previous_page_number()
        
        return self._replace_query_param(url, self.page_query_param, page_number)

    def _replace_query_param(self, url, key, value):
        """
        Dado un URL, reemplaza o agrega un parámetro y su valor.
        """
        # Separar la base de la URL de los parámetros de consulta
        base_url = url.split('?')[0]
        query_params = {}
        
        # Si hay parámetros de consulta, convertirlos a diccionario
        if '?' in url:
            query_string = url.split('?')[1]
            query_params = dict(param.split('=') for param in query_string.split('&'))
        
        # Actualizar o agregar el nuevo parámetro
        query_params[key] = value
        
        # Reconstruir la URL con los parámetros actualizados
        new_query = urlencode(query_params)
        return f"{base_url}?{new_query}" if new_query else base_url

class ProductFilter(filters.FilterSet):
    """
    Filtros para productos en caché.
    
    Ejemplos de uso:
    - Búsqueda general: ?search=texto (busca en nombre, tipo, familia, grupo, línea y código)
    - Búsqueda por código exacto: ?codigo=777789
    - Filtrar por tipo específico: ?tipo=Divisor
    - Filtrar por familia específica: ?familia=Mamparas
    - Filtrar por grupo específico: ?grupo=GEBESA
    - Filtrar por línea específica: ?linea=Zone
    - Filtrar productos activos/inactivos: ?activo=true
    
    Se pueden combinar todos los parámetros:
    - /api/v1/cotizador/productos/?search=metal&familia=Mamparas&page=1&page_size=20
    
    Búsqueda avanzada:
    - La búsqueda con ?search= ahora soporta múltiples palabras y devuelve resultados
      que contienen TODAS las palabras en cualquiera de los campos de búsqueda.
      Ejemplo: ?search=escritorio metal (encuentra productos que contengan ambas palabras)
    """
    search = filters.CharFilter(method='filter_search')
    codigo = filters.CharFilter(field_name='reference_mask', lookup_expr='exact')
    tipo = filters.CharFilter(field_name='type_name', lookup_expr='icontains')
    familia = filters.CharFilter(field_name='family_name', lookup_expr='icontains')
    grupo = filters.CharFilter(field_name='group_name', lookup_expr='icontains')
    linea = filters.CharFilter(field_name='line_name', lookup_expr='icontains')
    activo = filters.BooleanFilter(field_name='active')

    def filter_search(self, queryset, name, value):
        """
        Búsqueda que coincide con cualquier campo especificado
        """
        if not value or value.strip() == '':
            return queryset
            
        # Si el término de búsqueda tiene espacios, podemos buscar el término completo
        # y también dividirlo en palabras para búsquedas más específicas
        value = value.strip()
        
        # Primero intentamos buscar el término completo (incluyendo espacios)
        # Añadimos búsqueda exacta por código (reference_mask)
        complete_term_query = (
            Q(name__icontains=value) |
            Q(type_name__icontains=value) |
            Q(family_name__icontains=value) |
            Q(line_name__icontains=value) |
            Q(group_name__icontains=value) |
            Q(reference_mask__icontains=value) |
            Q(reference_mask__exact=value)  # Búsqueda exacta por código
        )
        
        # Si el término tiene espacios, también buscamos cada palabra por separado
        if ' ' in value:
            # Dividir el término en palabras y eliminar palabras vacías
            search_terms = [term for term in value.split() if term.strip()]
            
            if search_terms:
                # Construir una consulta que requiera que todas las palabras estén presentes
                multi_word_query = Q()
                
                for term in search_terms:
                    term_query = (
                        Q(name__icontains=term) |
                        Q(type_name__icontains=term) |
                        Q(family_name__icontains=term) |
                        Q(line_name__icontains=term) |
                        Q(group_name__icontains=term) |
                        Q(reference_mask__icontains=term)
                    )
                    # Combinar con AND para requerir que todas las palabras coincidan
                    multi_word_query &= term_query
                
                # Combinar ambas consultas con OR para encontrar coincidencias
                # ya sea con el término completo o con todas las palabras individuales
                return queryset.filter(complete_term_query | multi_word_query)
        
        # Si no hay espacios, simplemente usamos la consulta del término completo
        return queryset.filter(complete_term_query)

    class Meta:
        model = ProductsCache
        fields = ['search', 'codigo', 'tipo', 'familia', 'grupo', 'linea', 'activo']

class ProductsCacheViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para consultar productos en caché.
    Soporta:
    - Paginación:
      * Página actual: ?page=1
      * Tamaño de página: ?page_size=10 (máximo 100)
    - Búsqueda general con ?search= (busca en nombre, tipo, familia, grupo, línea y código)
    - Búsqueda exacta por código: ?codigo=777789
    - Filtros específicos por tipo, familia, grupo y línea
    - Filtro de productos activos/inactivos: ?activo=true o ?activo=false
    - Ordenamiento por cualquier campo
    
    Ejemplos de uso:
    - Paginación: 
      * /api/v1/cotizador/productos/?page=1&page_size=20
    - Búsqueda general: 
      * /api/v1/cotizador/productos/?search=escritorio
    - Búsqueda por código exacto:
      * /api/v1/cotizador/productos/?codigo=777789
    - Filtros específicos:
      * /api/v1/cotizador/productos/?tipo=Divisor
      * /api/v1/cotizador/productos/?familia=Mamparas
      * /api/v1/cotizador/productos/?grupo=Accesorios
      * /api/v1/cotizador/productos/?linea=Zone
      * /api/v1/cotizador/productos/?activo=true
    
    Se pueden combinar todos los parámetros:
    - /api/v1/cotizador/productos/?search=metal&familia=Mamparas&page=1&page_size=20
    
    Búsqueda avanzada:
    - La búsqueda con ?search= ahora soporta múltiples palabras y devuelve resultados
      que contienen TODAS las palabras en cualquiera de los campos de búsqueda.
      Ejemplo: ?search=escritorio metal (encuentra productos que contengan ambas palabras)
    """
    queryset = ProductsCache.objects.all()
    serializer_class = ProductsCacheSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ProductFilter
    pagination_class = CustomPagination
    ordering_fields = '__all__'
    ordering = ['name']
    
    def get_queryset(self):
        """
        Sobrescribe el método get_queryset para excluir productos con line_name 'Radiant' o 'Rapido'
        """
        queryset = super().get_queryset()
        # Excluir productos de las líneas Radiant y Rapido
        queryset = queryset.exclude(line_name__in=['Radiant', 'Rapido', 'Electrical'])
        return queryset

    def _parse_precios(self, precios_str):
        """Obtiene el precio base del producto como un float"""
        if not precios_str:
            return None
            
        try:
            for precio in precios_str.split('|'):
                if not precio:
                    continue
                    
                partes = precio.split(':')
                if len(partes) >= 2:
                    id_precio = partes[0]
                    valor = partes[1]
                    # Solo nos interesa el precio base
                    if id_precio == "Precio base":
                        return float(valor)
            return None
            
        except Exception:
            return None

    def _parse_ids_precios(self, ids_precios_str):
        """Convierte el string de ids_precios en un diccionario con valores float"""
        if not ids_precios_str:
            return {}
            
        try:
            ids_precios = {}
            for precio in ids_precios_str.split('|'):
                if not precio:
                    continue
                    
                partes = precio.split(':')
                if len(partes) >= 2:
                    id_precio = partes[0]
                    try:
                        valor = float(partes[1])
                        ids_precios[id_precio] = valor
                    except ValueError:
                        continue
                    
            # Solo retornar los IDs que nos interesan
            ids_filtrados = {k: v for k, v in ids_precios.items() if k in ['32', '43', '40', '33', '34', '38']}
            return ids_filtrados
            
        except Exception:
            return {}

    def _process_product_data(self, product):
        """Procesa y estructura los datos del producto"""
        return {
            "informacion_general": {
                "id_externo": product.get("id_externo"),
                "tmpl_id": product.get("tmpl_id"),
                "product_id": product.get("product_id"),
                "clave": product.get("clave"),
                "producto": product.get("producto"),
                "descripcion_venta": product.get("descripcion_venta"),
                "traduccion_producto": product.get("traduccion_producto"),
                "traduccion_template_producto": product.get("traduccion_template_producto")
            },
            "clasificacion": {
                "familia": {
                    "id": product.get("familia_id"),
                    "nombre": product.get("familia")
                },
                "grupo": {
                    "id": product.get("grupo_id"),
                    "nombre": product.get("grupo")
                },
                "linea": {
                    "id": product.get("linea_id"),
                    "nombre": product.get("linea")
                },
                "tipo": {
                    "id": product.get("tipo_id"),
                    "nombre": product.get("tipo")
                }
            },
            "atributos": {
                "atributos_str": product.get("atributos"),
                "ids_atributos": product.get("ids_atributos")
            },
            "precios": {
                "precio_base": self._parse_precios(product.get("precios")),
                "precios_unidades": self._parse_ids_precios(product.get("ids_precios"))
            },
            "empresa": {
                "id": product.get("id_empresa"),
                "nombre": product.get("nombre_empresa")
            },
            "sat": {
                "id": product.get("id_sat"),
                "codigo": product.get("codigo_sat"),
                "nombre": product.get("nombre_sat")
            },
            "medidas": {
                "uom": product.get("uom"),
                "medida_compra": product.get("medida_compra"),
                "medida_compra_tipo": product.get("medida_compra_tipo"),
                "medida_compra_factor": product.get("medida_compra_factor")
            },
            "peso_y_volumen": {
                "peso_bruto": product.get("peso_bruto"),
                "volumen": product.get("volumen")
            },
            "rutas": {
                "ruta_id": product.get("ruta_id"),
                "ruta_nombre": product.get("ruta_nombre"),
                "rutas_ids": product.get("rutas_ids")
            }
        }

    @action(detail=False, methods=['get'], url_path='detalles/(?P<clave>[^/.]+)')
    def get_details(self, request, clave=None):
        """
        Obtiene los detalles y datos del producto desde la API externa
        """
        if not clave:
            return Response(
                {"error": "Debe proporcionar una clave de producto"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # URL de la API externa
            api_url = "https://api2.ercules.mx/api/v1/common/product_data"
            
            # Parámetros de la consulta
            params = {
                "user_id": 2,
                "products": 0,
                "product_tmpl_ids": clave,
                "line_ids": 0,
                "group_ids": 0,
                "type_ids": 0,
                "family_ids": 0,
                "only_line": 1
            }

            # Realizar la petición a la API externa
            response = requests.get(api_url, params=params)
            
            # Verificar si la petición fue exitosa
            if response.status_code == 200:
                data = response.json()
                # Procesar cada producto en la respuesta
                processed_data = [self._process_product_data(product) for product in data]
                return Response(processed_data)
            else:
                return Response(
                    {"error": f"Error al consultar la API externa: {response.status_code}"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

        except requests.RequestException as e:
            return Response(
                {"error": f"Error de conexión: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {"error": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='precio/(?P<reference_mask>[^/.]+)')
    def precio(self, request, reference_mask=None):
        """
        Obtiene los detalles completos y precios de un producto por su reference_mask
        
        Ejemplo de uso:
        - /api/v1/cotizador/productos/precio/777789/
        """
        if not reference_mask:
            return Response(
                {"error": "Debe proporcionar un reference_mask de producto"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # URL de la API externa
            api_url = "https://api2.ercules.mx/api/v1/common/product_data"
            
            # Parámetros de la consulta
            params = {
                "user_id": 2,
                "products": 0,
                "product_tmpl_ids": reference_mask,
                "line_ids": 0,
                "group_ids": 0,
                "type_ids": 0,
                "family_ids": 0,
                "only_line": 1
            }

            # Realizar la petición a la API externa
            response = requests.get(api_url, params=params)
            
            # Verificar si la petición fue exitosa
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return Response(
                        {'error': f'No se encontró el producto con reference_mask: {reference_mask}'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
                # Procesar el primer producto en la respuesta
                processed_data = self._process_product_data(data[0])
                
                # Intentar obtener datos del caché si existen
                try:
                    cached_product = ProductsCache.objects.get(reference_mask=reference_mask)
                    processed_data['cache'] = {
                        'id': cached_product.id,
                        'reference_mask': cached_product.reference_mask,
                        'name': cached_product.name,
                        'image_url': cached_product.image_url,
                        'last_sync': cached_product.last_sync
                    }
                except ProductsCache.DoesNotExist:
                    processed_data['cache'] = None
                
                return Response(processed_data)
            else:
                return Response(
                    {"error": f"Error al consultar la API externa: {response.status_code}"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

        except requests.RequestException as e:
            return Response(
                {"error": f"Error de conexión: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Error al obtener la información: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def tipos(self, request):
        """
        Obtener lista única de tipos de productos
        """
        tipos = ProductsCache.objects.values_list('type_name', flat=True).distinct().order_by('type_name')
        return Response(list(tipos))

    @action(detail=False, methods=['get'])
    def lineas(self, request):
        """
        Obtener lista única de líneas de productos
        """
        lineas = ProductsCache.objects.values_list('line_name', flat=True).distinct().order_by('line_name')
        return Response(list(lineas))

    @action(detail=False, methods=['get'])
    def familias(self, request):
        """
        Obtener lista única de familias de productos
        """
        familias = ProductsCache.objects.values_list('family_name', flat=True).distinct().order_by('family_name')
        return Response(list(familias))

    @action(detail=False, methods=['get'])
    def grupos(self, request):
        """
        Obtener lista única de grupos de productos
        """
        grupos = ProductsCache.objects.values_list('group_name', flat=True).distinct().order_by('group_name')
        return Response(list(grupos))

    @action(detail=False, methods=['get'])
    def categorias(self, request):
        """
        Obtener todas las categorías (tipos, líneas, familias, grupos) en un solo request
        """
        tipos = ProductsCache.objects.values_list('type_name', flat=True).distinct().order_by('type_name')
        lineas = ProductsCache.objects.values_list('line_name', flat=True).distinct().order_by('line_name')
        familias = ProductsCache.objects.values_list('family_name', flat=True).distinct().order_by('family_name')
        grupos = ProductsCache.objects.values_list('group_name', flat=True).distinct().order_by('group_name')
        
        return Response({
            'tipos': list(tipos),
            'lineas': list(lineas),
            'familias': list(familias),
            'grupos': list(grupos)
        })

    @action(detail=False, methods=['get'], url_path='sin-imagenes')
    def sin_imagenes(self, request):
        """
        Obtiene una lista de productos que no tienen imágenes.
        
        Ejemplo de uso:
        - /api/v1/cotizador/productos/sin-imagenes/
        
        Soporta los mismos filtros y paginación que el endpoint principal.
        """
        # Filtrar productos sin imagen
        queryset = self.filter_queryset(self.get_queryset().filter(
            Q(image_url__isnull=True) | Q(image_url='')
        ))
        
        # Aplicar paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='cargar-imagen')
    def cargar_imagen(self, request):
        """
        Carga una imagen para un producto específico.
        
        Ejemplo de uso:
        - POST /api/v1/cotizador/productos/cargar-imagen/
        
        Parámetros:
        - image: Archivo de imagen (multipart/form-data)
        - reference_mask: Identificador único del producto
        
        Retorna:
        - URL de la imagen cargada
        - Información actualizada del producto
        """
        return self._procesar_carga_imagen(request)
    
    @action(detail=False, methods=['post'], url_path='cargar-imagenes')
    def cargar_imagenes(self, request):
        """
        Alias para cargar-imagen. Carga una imagen para un producto específico.
        
        Ejemplo de uso:
        - POST /api/v1/cotizador/productos/cargar-imagenes/
        
        Parámetros:
        - image: Archivo de imagen (multipart/form-data)
        - reference_mask: Identificador único del producto
        
        Retorna:
        - URL de la imagen cargada
        - Información actualizada del producto
        """
        return self._procesar_carga_imagen(request)
    
    def _procesar_carga_imagen(self, request):
        """
        Método interno para procesar la carga de imágenes.
        Usado por los endpoints cargar-imagen y cargar-imagenes.
        """
        serializer = ProductImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos validados
        image_file = serializer.validated_data['image']
        reference_mask = serializer.validated_data['reference_mask']
        
        # Obtener el producto
        product = ProductsCache.objects.filter(reference_mask=reference_mask).first()
        if not product:
            return Response(
                {"error": f"No se encontró ningún producto con reference_mask: {reference_mask}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Subir la imagen a Supabase Storage
        image_url, error = upload_image_to_supabase(
            image_file=image_file,
            line_name=product.line_name or "otros",
            reference_mask=reference_mask
        )
        
        if error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Actualizar o crear el registro en CotizadorImagenproducto
        imagen_producto, created = CotizadorImagenproducto.objects.update_or_create(
            clave_padre=reference_mask,
            defaults={'url': image_url}
        )
        
        # Actualizar el campo image_url en Supabase
        try:
            supabase: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            
            result = supabase.table('products_cache').update(
                {"image_url": image_url}
            ).eq('reference_mask', reference_mask).execute()
            
            # Actualizar el objeto local para la respuesta
            product.image_url = image_url
            product.save()
            
        except Exception as e:
            # Si falla la actualización en Supabase, al menos tenemos la imagen en CotizadorImagenproducto
            return Response({
                "warning": f"La imagen se cargó correctamente, pero no se pudo actualizar en Supabase: {str(e)}",
                "image_url": image_url,
                "product": ProductsCacheSerializer(product).data
            }, status=status.HTTP_207_MULTI_STATUS)
        
        return Response({
            "message": "Imagen cargada y actualizada correctamente",
            "image_url": image_url,
            "product": ProductsCacheSerializer(product).data
        }, status=status.HTTP_200_OK)
