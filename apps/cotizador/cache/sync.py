from django.db import connections
from supabase import create_client, Client
from django.conf import settings
from decimal import Decimal
import time
import logging
from datetime import datetime

def sync_products_to_supabase():
    """
    Sincroniza los productos desde PostgreSQL a Supabase.
    """
    print("Iniciando sincronización de productos...")
    
    # Configuración de Supabase
    print("Conectando a Supabase...")
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )

    # Estadísticas
    total_products = 0
    successful_products = 0
    products_with_images = 0
    preserved_images = 0
    start_time = datetime.now()

    # Obtener datos de PostgreSQL
    print("Obteniendo productos de la base de datos ERP...")
    with connections['erp-portalgebesa-com'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                pt.id,
                pt.reference_mask,
                pt.note_pricelist,  
                pt.type_id,
                pt.family_id,
                pt.line_id,
                pt.group_id,
                pt.is_line,
                pt.pricelist,
                pt.active,
                -- Nueva columna "code"
                COALESCE(pt.reference_mask, pt.note_pricelist) AS code,
                -- Información adicional de las tablas relacionadas
                ptype.name   AS type_name,
                pfam.name    AS family_name,
                pline.name   AS line_name,
                pgroup.name  AS group_name,
                -- Nueva columna con la traducción en español
                it.value AS name_spanish
            FROM product_template pt
                LEFT JOIN product_type ptype 
                    ON pt.type_id = ptype.id
                LEFT JOIN product_family pfam 
                    ON pt.family_id = pfam.id
                LEFT JOIN product_line pline 
                    ON pt.line_id = pline.id
                LEFT JOIN product_group pgroup 
                    ON pt.group_id = pgroup.id
                -- Agrega la unión con ir_translation para obtener la traducción en español
                LEFT JOIN ir_translation it 
                    ON it.res_id = pt.id
                       AND it.name = 'product.template,name'
                       AND it.lang = 'es_MX'
            WHERE 
                pt.is_line = TRUE
                AND pt.active = TRUE
                AND (
                    (
                        pt.reference_mask IS NOT NULL
                        AND pt.reference_mask NOT IN (
                            'LLR1SCANT', 'LLR1SCANTWM', 'LLRBLAPMBBFLPF162329NT', 
                            'LLRBLAPMFFLPF162329NT', 'LLRBLAPMSBBFLPF162329NT', 
                            'LLRBLAPMSFFLPF162329NT', 'LLRBPMBBFLPF162329NT', 
                            'LLRBPMFFLPF162329NT', 'LLRBPMSBBFLPF162329NT', 
                            'LLRBPMSFFLPF162329NT', 'LLRBWSLP242442', 'LLRBWSLP302442', 
                            'LLRBWSRELP242442', 'LLRBWSRELP302442', 'LLRBWSSLP2460', 
                            'LLRBWSSLP2465', 'LLRBWSSLP2472', 'LLRBWSSLP3060', 
                            'LLRBWSSLP3065', 'LLRBWSSLP3072', 'LLRC1DLP602024', 
                            'LLRC1DLP712024', 'LLRCANTSS', 'LLRCANTSSWM', 'LLRCC2720', 
                            'LLRCOUNTBR', 'LLRCRBRKIT', 'LLRCWSSLP363624', 'LLRCWSSLP423624', 
                            'LLRCWSSLP424224', 'LLRCWSSLP424230', 'LLRCWSSLP483624', 
                            'LLRCWSSLP484224', 'LLRCWSSLP484230', 'LLRCWSSLP484824', 
                            'LLRCWSSLP484830', 'LLRCWSSLP603624', 'LLRCWSSLP604224', 
                            'LLRCWSSLP604230', 'LLRCWSSLP604824', 'LLRCWSSLP604830', 
                            'LLREHWSLP367224', 'LLREHWSLP367230', 'LLREIWSLP2460', 
                            'LLREIWSLP2472', 'LLREIWSLP3072', 'LLREL01525MPS120', 
                            'LLREL01525MPS72', 'LLREL01525S120', 'LLREL01525S72', 
                            'LLREL0153611SMAM172', 'LLREL0153611SMBM172', 
                            'LLREL0153611SMCM172', 'LLREL0153620SMA72', 
                            'LLREL0153620SMB72', 'LLREL0153620SMC72', 'LLREL0181922E120', 
                            'LLREL0181922E72', 'LLREL01820M22120', 'LLREL01820M2272', 
                            'LLREL01820M22D172', 'LLREL01820M2X22120', 'LLREL01820M2X2272', 
                            'LLREL01820M2X22U5/U5120', 'LLREL01820M2X22U5/U572', 
                            'LLREL01820M2X40120', 'LLREL01820M2X4072', 
                            'LLREL01826M3X4002120', 'LLREL01826M3X400272', 
                            'LLREL01826M4X4001120', 'LLREL01826M4X400172', 'LLREL02137C1172', 
                            'LLREL02137C2072', 'LLREL0251122120', 'LLREL025112272', 
                            'LLREL0251133120', 'LLREL025113372', 'LLREL02511B22U572', 
                            'LLREL02511B31U172', 'LLREL02511B33U3172', 'LLREL02511B4072', 
                            'LLREL0252022XA120', 'LLREL0252022XA72', 'LLREL0252022YA120', 
                            'LLREL0252022YA72', 'LLREL0252022Z120', 'LLREL0252022Z72', 
                            'LLREL0252033XA120', 'LLREL0252033XA72', 'LLREL0252033YA120', 
                            'LLREL0252033YA72', 'LLREL0252033Z120', 'LLREL0252033Z72', 
                            'LLREL0335911120', 'LLREL033591172', 'LLREL0335911M1120', 
                            'LLREL0335911M172', 'LLREL0335920120', 'LLREL033592072', 
                            'LLREL03373EN22120', 'LLREL03373EN2272', 'LLREL03373EN22M2120', 
                            'LLREL03373EN22M272', 'LLREL03373GN22M1120', 
                            'LLREL03373GN22M172', 'LLREL03373GN31M1120', 
                            'LLREL03373GN31M172', 'LLREL03373TT40120', 'LLREL03373TT4072', 
                            'LLREL03378GN22120', 'LLREL03378GN2272', 'LLREL03378GN22M1120', 
                            'LLREL03378GN22M172', 'LLREL03378GN22M2120', 
                            'LLREL03378GN22M272', 'LLREL03378GN31120', 'LLREL03378GN3172', 
                            'LLREL03378GN31M1120', 'LLREL03378GN31M172', 'LLREL03378GN40120', 
                            'LLREL03378GN4072', 'LLREL03378TT22MMT120', 'LLREL03378TT22MMT72', 
                            'LLREL03378TT40120', 'LLREL03378TT4072', 'LLREL0338522120', 
                            'LLREL033852272', 'LLREL0338522M1120', 'LLREL0338522M172', 
                            'LLREL0338522M2120', 'LLREL0338522M272', 'LLREL0338531120', 
                            'LLREL033853172', 'LLREL0338531M1120', 'LLREL0338531M172', 
                            'LLREL0338540120', 'LLREL033854072', 'LLREL0377021MR1120', 
                            'LLREL0377021MR172', 'LLREL0377030120', 'LLREL037703072', 
                            'LLREL0381621MR1120', 'LLREL0381621MR172', 'LLREL0381630120', 
                            'LLREL038163072', 'LLREL0407311AMR172', 'LLREL0407320A72', 
                            'LLREL0407321AMR172', 'LLREL0407330A72', 'LLREL0407332AMR272', 
                            'LLREL0407350A72', 'LLREL0407611UB172', 'LLREL040762072', 
                            'LLREL0407621UB172', 'LLREL040763072', 'LLREL0407632UB272', 
                            'LLREL040765072', 'LLREL04262A11UB148', 'LLREL04262A11UB160', 
                            'LLREL04262S11UB1120', 'LLREL04262S11UB172', 'LLREL0428611M1120', 
                            'LLREL0428611M172', 'LLREL0428620120', 'LLREL042862072', 
                            'LLREL0431511AA120', 'LLREL0431511AA72', 'LLREL0431511AZ120', 
                            'LLREL0431511AZ72', 'LLREL0431520A120', 'LLREL0431520A72', 
                            'LLREL0431520Z120', 'LLREL0431520Z72', 'LLREL0431521AA120', 
                            'LLREL0431521AA72', 'LLREL0431521AZ120', 'LLREL0431521AZ72', 
                            'LLREL0431530A120', 'LLREL0431530A72', 'LLREL0431530Z72', 
                            'LLREL0431532AA120', 'LLREL0431532AA72', 'LLREL0431532AZ120', 
                            'LLREL0431532AZ72', 'LLREL0431550A120', 'LLREL0431550A72', 
                            'LLREL0431550Z120', 'LLREL0431550Z72', 'LLREL0475572', 
                            'LLREL0475672', 'LLREL0481431U172', 'LLREL05451A110', 
                            'LLREL05451A111', 'LLREL05451A112', 'LLREL05451A113', 
                            'LLREL05451A114', 'LLREL05451A115', 'LLREL05451A116', 
                            'LLREL05451A117', 'LLREL0806232', 'LLREL0806832', 'LLREL080863', 
                            'LLREL080923', 'LLREL081803', 'LLREL420813', 'LLREL420823', 
                            'LLREL5241332', 'LLREL524263C', 'LLREL524263G', 'LLREL524633', 
                            'LLREL524903', 'LLREPTWSLP367224', 'LLREPTWSLP367230', 
                            'LLREPWSLP367224', 'LLREPWSLP367230', 'LLREWSCCLP363624', 
                            'LLREWSCCLP423624', 'LLREWSCCLP424224', 'LLREWSCCLP424230', 
                            'LLREWSCCLP483624', 'LLREWSCCLP484224', 'LLREWSCCLP484230', 
                            'LLREWSCCLP484824', 'LLREWSCCLP484830', 'LLREWSCCLP603624', 
                            'LLREWSCCLP604224', 'LLREWSCCLP604230', 'LLREWSCCLP604824', 
                            'LLREWSCCLP604830', 'LLREWSLP2424', 'LLREWSLP2430', 
                            'LLREWSLP2436', 'LLREWSLP2442', 'LLREWSLP2448', 'LLREWSLP3024', 
                            'LLREWSLP3030', 'LLREWSLP3036', 'LLREWSLP3042', 'LLREWSLP3048'
                        )
                    )
                    OR (pt.reference_mask IS NULL AND pt.pricelist = TRUE)
                )
        """)
        
        columns = [desc[0] for desc in cursor.description]
        
        print("Procesando y sincronizando productos...")
        batch_size = 100
        current_batch = []
        
        # Obtener un mapa de los productos existentes en Supabase para preservar las URLs de imágenes
        print("Obteniendo productos existentes en Supabase para preservar imágenes...")
        try:
            existing_products_result = supabase.table('products_cache').select('reference_mask,image_url').execute()
            existing_products_map = {}
            if existing_products_result.data:
                for product in existing_products_result.data:
                    if product.get('reference_mask') and product.get('image_url'):
                        existing_products_map[product['reference_mask']] = product['image_url']
                print(f"Se encontraron {len(existing_products_map)} productos con imágenes en Supabase")
        except Exception as e:
            print(f"Error al obtener productos existentes: {str(e)}")
            existing_products_map = {}
        
        for row in cursor.fetchall():
            total_products += 1
            
            try:
                # Convertir a diccionario
                product = dict(zip(columns, row))
                
                # Validar datos requeridos
                if not product['id']:
                    raise ValueError(f"ID faltante para el producto: {product.get('name_spanish', 'N/A')}")
                
                # Si reference_mask es nulo, usar note_pricelist
                if product['reference_mask'] is None and product.get('note_pricelist'):
                    product['reference_mask'] = product['note_pricelist']
                
                # Filtrar solo los campos que existen en la tabla products_cache
                allowed_fields = [
                    'id', 'name_spanish', 'reference_mask', 'type_id', 'family_id', 
                    'line_id', 'group_id', 'type_name', 'family_name', 
                    'line_name', 'group_name', 'is_line', 'active', 
                    'default_code', 'description_sale', 'image_url', 'last_sync'
                ]
                
                # Crear un nuevo diccionario con solo los campos permitidos y mapear name_spanish a name
                filtered_product = {}
                for field in allowed_fields:
                    if field in product:
                        if field == 'name_spanish':
                            filtered_product['name'] = product[field]  # Usar name_spanish como name
                        else:
                            filtered_product[field] = product[field]
                
                # Verificar si el producto tiene una URL de imagen en Supabase
                has_existing_image = False
                if filtered_product.get('reference_mask') and filtered_product['reference_mask'] in existing_products_map:
                    filtered_product['image_url'] = existing_products_map[filtered_product['reference_mask']]
                    has_existing_image = True
                    preserved_images += 1
                    print(f"Preservando imagen para {filtered_product['reference_mask']}: {filtered_product['image_url']}")
                
                # Si no tiene imagen existente, intentar obtenerla de cotizador_imagenproducto
                if not has_existing_image and filtered_product.get('reference_mask'):
                    image_result = supabase.table('cotizador_imagenproducto')\
                        .select('url')\
                        .eq('clave_padre', filtered_product['reference_mask'])\
                        .execute()
                    
                    # Agregar URL de imagen si existe
                    if image_result.data:
                        filtered_product['image_url'] = image_result.data[0]['url']
                        products_with_images += 1
                    else:
                        filtered_product['image_url'] = None
                elif not has_existing_image:
                    filtered_product['image_url'] = None
                
                # Agregar timestamp
                filtered_product['last_sync'] = datetime.now().isoformat()
                
                current_batch.append(filtered_product)
                
                # Si alcanzamos el tamaño del lote, sincronizar
                if len(current_batch) >= batch_size:
                    try:
                        batch_number = total_products // batch_size
                        print(f"Sincronizando lote {batch_number} ({len(current_batch)} productos)...")
                        
                        # Eliminar duplicados en el lote basado en reference_mask
                        unique_batch = {}
                        for item in current_batch:
                            if item.get('reference_mask'):  # Solo incluir si tiene reference_mask (que puede venir de note_pricelist)
                                unique_batch[item['reference_mask']] = item
                            else:
                                print(f" Advertencia: Producto ID {item.get('id')} sin reference_mask ni note_pricelist")
                        unique_batch = list(unique_batch.values())
                        
                        if unique_batch:
                            result = supabase.table('products_cache').upsert(unique_batch, on_conflict='reference_mask').execute()
                            
                            if result.data:
                                successful_products += len(unique_batch)
                                print(f" Lote {batch_number} sincronizado")
                            else:
                                raise Exception("No se recibió confirmación de Supabase")
                        else:
                            print(f" Lote {batch_number} no contenía productos válidos para sincronizar")
                            
                    except Exception as e:
                        print(f" Error en lote {batch_number}: {str(e)}")
                    
                    # Limpiar el lote actual
                    current_batch = []
                    
                    # Pequeña pausa para evitar sobrecarga
                    time.sleep(0.5)
                
            except Exception as e:
                print(f" Error en producto {row[2] if len(row) > 2 else 'desconocido'}: {str(e)}")

        # Sincronizar el último lote si quedaron productos
        if current_batch:
            try:
                print(f"\nSincronizando lote final ({len(current_batch)} productos)...")
                
                # Eliminar duplicados en el lote final basado en reference_mask
                unique_batch = {}
                for item in current_batch:
                    if item.get('reference_mask'):  # Solo incluir si tiene reference_mask (que puede venir de note_pricelist)
                        unique_batch[item['reference_mask']] = item
                    else:
                        print(f" Advertencia: Producto ID {item.get('id')} sin reference_mask ni note_pricelist")
                unique_batch = list(unique_batch.values())
                
                if unique_batch:
                    result = supabase.table('products_cache').upsert(unique_batch, on_conflict='reference_mask').execute()
                    
                    if result.data:
                        successful_products += len(unique_batch)
                        print(" Lote final sincronizado")
                    else:
                        raise Exception("No se recibió confirmación de Supabase")
                else:
                    print(" Lote final no contenía productos válidos para sincronizar")
                    
            except Exception as e:
                print(f" Error en lote final: {str(e)}")

        # Mostrar resumen
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n=== Resumen de Sincronización ===")
        print(f"Tiempo total: {duration}")
        print(f"Productos en ERP: {total_products}")
        print(f"Productos sincronizados: {successful_products}")
        print(f"Productos con imágenes: {products_with_images}")
        print(f"Imágenes preservadas: {preserved_images}")
        print(f"Productos sin imágenes: {total_products - products_with_images - preserved_images}")
        
        if successful_products < total_products:
            print(f" No se sincronizaron {total_products - successful_products} productos")
        
        return {
            "total": total_products,
            "successful": successful_products,
            "with_images": products_with_images,
            "preserved_images": preserved_images,
            "duration": str(duration)
        }

def sync_clients_to_supabase(clients_data):
    """
    Sincroniza los clientes desde la API de Odoo a Supabase.
    
    Args:
        clients_data (list): Lista de diccionarios con los datos de los clientes
        
    Returns:
        dict: Estadísticas de la sincronización
    """
    print("Iniciando sincronización de clientes a Supabase...")
    
    # Configuración de Supabase
    print("Conectando a Supabase...")
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )

    # Estadísticas
    total_clients = len(clients_data)
    successful_clients = 0
    error_count = 0
    start_time = datetime.now()
    
    if not clients_data:
        print("No hay clientes para sincronizar")
        return {
            'total': 0,
            'successful': 0,
            'errors': 0,
            'duration': "0:00:00"
        }
    
    print(f"Procesando {total_clients} clientes...")
    
    # Procesar los clientes en lotes para evitar sobrecarga
    batch_size = 50
    current_batch = []
    
    for client in clients_data:
        try:
            # Verificar que el cliente tenga partner_id
            if not client.get('partner_id'):
                print(f"Cliente sin partner_id: {client}")
                error_count += 1
                continue
            
            # Filtrar solo los campos que necesitamos
            filtered_client = {
                'partner_id': client.get('partner_id'),
                'name_partner': client.get('name_partner', ''),
                'rfc': client.get('rfc', '')
            }
            
            current_batch.append(filtered_client)
            
            # Si alcanzamos el tamaño del lote, sincronizar
            if len(current_batch) >= batch_size:
                try:
                    batch_number = (successful_clients + error_count) // batch_size
                    print(f"Sincronizando lote {batch_number} ({len(current_batch)} clientes)...")
                    
                    # Eliminar duplicados en el lote basado en partner_id
                    unique_batch = {}
                    for item in current_batch:
                        if item.get('partner_id'):
                            unique_batch[item['partner_id']] = item
                        else:
                            print(f" Advertencia: Cliente sin partner_id")
                    unique_batch = list(unique_batch.values())
                    
                    if unique_batch:
                        result = supabase.table('cotizador_cliente').upsert(unique_batch, on_conflict='partner_id').execute()
                        
                        if result.data:
                            successful_clients += len(unique_batch)
                            print(f" Lote {batch_number} sincronizado")
                        else:
                            raise Exception("No se recibió confirmación de Supabase")
                    else:
                        print(f" Lote {batch_number} no contenía clientes válidos para sincronizar")
                        
                except Exception as e:
                    print(f" Error en lote {batch_number}: {str(e)}")
                    error_count += len(current_batch)
                
                # Limpiar el lote actual
                current_batch = []
                
                # Pequeña pausa para evitar sobrecarga
                time.sleep(0.5)
            
        except Exception as e:
            print(f" Error en cliente {client.get('partner_id', 'desconocido')}: {str(e)}")
            error_count += 1
    
    # Sincronizar el último lote si quedaron clientes
    if current_batch:
        try:
            print(f"\nSincronizando lote final ({len(current_batch)} clientes)...")
            
            # Eliminar duplicados en el lote final basado en partner_id
            unique_batch = {}
            for item in current_batch:
                if item.get('partner_id'):
                    unique_batch[item['partner_id']] = item
                else:
                    print(f" Advertencia: Cliente sin partner_id")
            unique_batch = list(unique_batch.values())
            
            if unique_batch:
                result = supabase.table('cotizador_cliente').upsert(unique_batch, on_conflict='partner_id').execute()
                
                if result.data:
                    successful_clients += len(unique_batch)
                    print(" Lote final sincronizado")
                else:
                    raise Exception("No se recibió confirmación de Supabase")
            else:
                print(" Lote final no contenía clientes válidos para sincronizar")
                
        except Exception as e:
            print(f" Error en lote final: {str(e)}")
            error_count += len(current_batch)
    
    # Mostrar resumen
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n=== Resumen de Sincronización de Clientes ===")
    print(f"Tiempo total: {duration}")
    print(f"Clientes totales: {total_clients}")
    print(f"Clientes sincronizados: {successful_clients}")
    print(f"Errores: {error_count}")
    
    if successful_clients < total_clients:
        print(f" No se sincronizaron {total_clients - successful_clients} clientes")
    
    return {
        'total': total_clients,
        'successful': successful_clients,
        'errors': error_count,
        'duration': str(duration)
    }

def get_clients_from_supabase():
    """
    Obtiene todos los clientes desde Supabase.
    
    Returns:
        list: Lista de diccionarios con los datos de los clientes
    """
    print("Obteniendo clientes desde Supabase...")
    
    # Configuración de Supabase
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    
    try:
        # Consultar todos los clientes
        result = supabase.table('cotizador_cliente').select('*').execute()
        
        if result.data:
            print(f"Se encontraron {len(result.data)} clientes en Supabase")
            return result.data
        else:
            print("No se encontraron clientes en Supabase")
            return []
            
    except Exception as e:
        print(f"Error al obtener clientes desde Supabase: {str(e)}")
        return []
