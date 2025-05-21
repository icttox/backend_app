from xml.etree import ElementTree as ET

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import os
import requests
import json

#Importamos la tabla de productos del cotizador para poder consultar la descripcion en espaniol
from apps.cotizador.cache.models import ProductsCache


if not settings.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurado")
os.environ['OPENAI_API_KEY'] = settings.OPENAI_API_KEY

# Usamos directamente la API de OpenAI en lugar de agents
from openai import OpenAI
import asyncio



# Inicializamos el cliente de OpenAI
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Instrucciones para el modelo de traducción
TRADUCTOR_INSTRUCCIONES = """
Eres un traductor especializado en mobiliario. Tu tarea es traducir nombres de productos del inglés al español de manera concisa y directa.
Debes mantener la traducción breve, similar a la longitud del texto original.
Incluye las medidas convertidas a centímetros cuando sea necesario (1 pulgada = 2.54 cm).
No agregues información adicional ni elabores descripciones largas.

Ejemplos:
- 'Height Changing Set, Synergy' → 'Kit de Cambio de Altura para Poste Synergy'
- '60" Stiffener, for 72" desk G Connect Aluminum' → 'Refuerzo (151 cm) p/Cubierta 180 cm G Connect Aluminio Text'
"""

def obtener_descripcion_agente(xml_description, odoo_description, context):
    """
    Traduce la descripción del producto del inglés al español usando la API de OpenAI.
    """
    # Si ya tenemos una descripción en Odoo, la usamos
    if odoo_description and odoo_description.strip():
        return odoo_description
    
    # Si no hay descripción en XML o está vacía, retornamos vacío
    if not xml_description or not xml_description.strip():
        return xml_description
    
    try:
        # Preparamos el prompt para la API de OpenAI
        prompt = f"Traduce este nombre de producto del inglés al español de manera concisa y directa: '{xml_description}'\nRecuerda incluir las medidas en centímetros cuando sea necesario y mantener la traducción breve."
        
        # Llamamos a la API de OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",  # Usando el modelo GPT-4o para mayor precisión
            messages=[
                {"role": "system", "content": TRADUCTOR_INSTRUCCIONES},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Valor bajo para respuestas más consistentes
            max_tokens=100    # Limitamos la longitud de la respuesta
        )
        
        # Extraemos y retornamos la traducción
        traduccion = response.choices[0].message.content.strip()
        return traduccion
    
    except Exception as e:
        # En caso de error, registramos el error y devolvemos la descripción original
        print(f"Error al traducir con OpenAI: {str(e)}")
        return xml_description  # Fallback a la descripción original

#allow any para pruebas
from rest_framework.permissions import AllowAny

class UploadAIPXMLView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        xml_file = request.FILES.get('file')
        if not xml_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        # Por ahora solo leemos el nombre y tamaño

        xml_content = xml_file.read()
        try:
            # Parsear el XML
            ns = {'ofda': 'http://www.ofdaxml.org/schema'}
            root = ET.fromstring(xml_content)

            items = []
            line_number = 1
            part_number_set = set()

            for oli in root.findall('.//ofda:OrderLineItem', ns):
                #Extraer cantidad y precios
                quantity = oli.findtext('ofda:Quantity',default='', namespaces=ns)
                line_item_number = oli.findtext('ofda:LineItemNumber',default='', namespaces=ns)
                #Precios
                price_element = oli.find('ofda:Price', ns)
                list_price = price_element.findtext('ofda:PublishedPrice',default='', namespaces=ns) if price_element is not None else ''
                extended = price_element.findtext('ofda:PublishedPriceExt',default='', namespaces=ns) if price_element is not None else ''
                #Tag
                tag = ''
                for tag_element in oli.findall('ofda:Tag', ns):
                    type_tag = tag_element.findtext('ofda:Type', default='', namespaces=ns)
                    if type_tag.strip() == 'Tag':

                        tag_value = tag_element.findtext('ofda:Value', default='', namespaces=ns)
                        tag = tag_value.strip() if tag_value else ''
                        break
                # Forzar a string si por error es un objeto XML
                if not isinstance(tag, str):
                    tag = ''

                #Extraer los datos del producto
                spec_item = oli.find('ofda:SpecItem', ns)
                part_number = ''
                description = ''
                catalog_code = ''
                catalog_location = ''
                if spec_item is not None:
                    part_number = ''
                    for tag_spec in spec_item.findall('ofda:Tag', ns):
                        type_tag = tag_spec.findtext('ofda:Type',default='', namespaces=ns)
                        tag_number = tag_spec.findtext('ofda:Number',default='', namespaces=ns)
                        if type_tag == 'NumberAndOptions' and tag_number:
                            part_number = tag_number
                            break
                    if not part_number:
                        part_number = spec_item.findtext('ofda:Number',default='', namespaces=ns)
                    description = spec_item.findtext('ofda:Description',default='', namespaces=ns)
                    opt_descriptions = []
                    for opt in spec_item.findall('ofda:Option', ns):
                        opt_desc = opt.findtext('ofda:Description',default='', namespaces=ns)
                        if opt_desc:
                            opt_descriptions.append(opt_desc)
                    full_description = description 
                    if opt_descriptions:
                        full_description += ' ' + ' '.join(opt_descriptions)

                    # Obtener código de catálogo (ej. SYN, CSG)
                    catalog_code = spec_item.findtext('ofda:Catalog/ofda:Code', default='', namespaces=ns)

                    # Obtener CatalogLocation si existe
                    for ud in spec_item.findall('ofda:UserDefined', ns):
                        if ud.attrib.get('Type') == 'CatalogLocation':
                            catalog_location = (ud.text or '').strip()
                            break
                if part_number:
                    part_number_set.add(part_number)   

                
                items.append({
                    'line_number': line_item_number or line_number,
                    'qty': quantity,
                    'part_number': part_number,
                    'description': full_description,
                    'tag': tag,
                    'catalog_code': catalog_code,
                    'catalog_location': catalog_location,
                    'list_price': list_price,
                    'extended': extended
                })
                line_number += 1
            
            part_numbers = list(part_number_set)
            print("PART NUMBERS EXTRAÍDOS DEL XML:", part_numbers)

            claves_completas = []
            claves_incompletas = []

            for pn in part_numbers:
                if '.' in pn:
                    is_incomplete = True
                    clean_pn = pn.rsplit('.')
                    print("PN LIMPIO:", clean_pn)
                    claves_incompletas.append(clean_pn[0])
                else:
                    claves_completas.append(pn)

            print("Claves completas:", claves_completas)
            print("Claves incompletas:", claves_incompletas)

            products = ProductsCache.objects.filter(reference_mask__in=claves_incompletas)
            products_dict = {p.reference_mask: p for p in products}

            if claves_completas:
                products_param = ",".join(claves_completas)
                api_url = f"https://api2.ercules.mx/api/v1/common/product_data?user_id=2&products={products_param}&product_tmpl_ids=0&line_ids=0&group_ids=0&type_ids=0&family_ids=0&only_line=1"
                
                try:
                    print(f"Llamando a la API con URL: {api_url}")
                    response = requests.get(api_url)
                    if response.status_code == 200:  
                        api_response = response.json()
                        print(f"Respuesta de la API")

                        api_products = {}
                        for product_data in api_response:
                            clave = product_data.get('clave', '')
                            if clave:
                                api_products[clave] = {
                                    'name': product_data.get('traduccion_producto', ''),
                                    'line_name': product_data.get('linea', ''),
                                }
                        print("Productos de API PROCESADOS:", api_products)
                except Exception as e:
                    print(f"Error al obtener datos de productos: {str(e)}")
                    api_products = {}
            else:
                api_products = {}
            



            print("\n===================================:")
            print("PRODUCTOS  SUPABASE:", products_dict)   
            print("\n===================================:")
            for reference_mask, product in products_dict.items():
                print("reference_mask:", reference_mask)
                print("description:", product.name)
                print("line_name:", product.line_name)
            print("===================================:")


            for item in items:
                xml_description = item.get('description', '')
                odoo_description = item.get('odoo_description', '')
                context = ( 
                    f"Línea: {item.get('line_number', '')}\n"
                    f"Clave: {item.get('part_number', '')}\n"
                    f"Línea de nombre: {item.get('line_name', '')}\n"
                    f"Tag: {item.get('tag', '')}\n"
                    f"Cantidad: {item.get('qty', '')}\n"
                    f"Precio de lista: {item.get('list_price', '')}\n"
                    f"Precio extendido: {item.get('extended', '')}\n"
                )
                part_number = item['part_number']
                product = None
                is_incomplete = False
                api_product = None

                if '.' in part_number:
                    is_incomplete = True
                    clean_pn = part_number.rsplit('.')[0]
                    print("PN LIMPIO:", clean_pn)
                    product = products_dict.get(clean_pn)
                else:
                    product = products_dict.get(part_number)
                    api_product = api_products.get(part_number)
                    print(f"Buscamdo {part_number} api:", api_product)

                # Asignar valores predeterminados para evitar None
                item['odoo_description'] = ''
                item['line_name'] = ''
                
                if product:
                    # Si se encuentra en la base de datos local
                    item['odoo_description'] = product.name + (" (clave incompleta)" if is_incomplete else "")
                    item['line_name'] = product.line_name # Intento 1: Llenar desde caché
                
                # Solo buscar en API si no se encontró en caché (para claves completas)
                if not product and api_product:
                    # Si se encuentra en la API externa
                    item['odoo_description'] = api_product.get('name', '')
                    # Solo llenar desde API si la caché no lo hizo
                    if not item['line_name']:
                        item['line_name'] = api_product.get('line_name', '') # Intento 2: Llenar desde API
                
                # Fallback si la descripción aún está vacía (no vino de caché ni API)
                if not item['odoo_description']:
                    # Si no se encuentra en ninguna fuente, usar el agente de IA para generar una traducción concisa
                    ai_description = obtener_descripcion_agente(item.get('description', ''), None, "")
                    # Eliminar comillas simples que podrían causar problemas en la serialización JSON
                    if ai_description:
                        ai_description = ai_description.replace("'", "")
                    item['odoo_description'] = ai_description + " (traducción AI)"
                    
                # Fallback si line_name aún está vacío (no vino de caché ni API)
                if not item['line_name']:
                    # 1) Intentar derivar directamente de CatalogLocation
                    catalog_loc = item.get('catalog_location', '')
                    if catalog_loc:
                        first_segment = catalog_loc.split('>')[0].strip()
                        if first_segment:
                            item['line_name'] = first_segment

                # 2) Intentar con diccionario de códigos de catálogo si sigue vacío
                if not item['line_name']:
                    catalog_map = {
                        'SYN': 'Synergy',
                        'ASC': 'Ascend',
                    }
                    code_upper = item.get('catalog_code', '').upper()
                    if code_upper in catalog_map:
                        item['line_name'] = catalog_map[code_upper]

                # 3) Último fallback usando CatalogLocation/Tag/Descripción buscando palabras clave
                if not item['line_name']:
                    location_text = (item.get('catalog_location') or item.get('tag') or '').lower()
                    description_lower = item.get('description', '').lower()

                    candidates = location_text + ' ' + description_lower

                    if 'synergy' in candidates:
                        item['line_name'] = 'Synergy'
                    elif 'prime' in candidates:
                        item['line_name'] = 'Prime'
                    elif 'ascend' in candidates:
                        item['line_name'] = 'Ascend'
                    elif 'optimus' in candidates:
                        item['line_name'] = 'Optimus'
                    elif 'g connect' in candidates or 'gconnect' in candidates:
                        item['line_name'] = 'G Connect'
                    elif 'phase' in candidates and ('arnes' in candidates or 'harness' in candidates):
                        item['line_name'] = 'Arneses'
                    elif 'gant' in candidates:
                        item['line_name'] = 'Gant'
                    else:
                        item['line_name'] = 'Sin categoría'
                
                # Imprimir información de depuración (una sola vez)
                print("-----------------------------------")
                print(f"Item procesado: {item}")
                print(f"Tag del item: {item.get('tag', '')}")
                print(f"Clave del item: {item.get('part_number', '')}")
                print(f"description del item: {item.get('description', '')}")
                print(f"odoo_description del item: {item.get('odoo_description', '')}")
                print(f"line_name del item: {item.get('line_name', '')}")
                print("-----------------------------------")




            return Response({
                'filename': xml_file.name,
                'items': items,
                'message': 'Archivo recibido correctamente, se encontraron {} items'.format(len(items))
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
