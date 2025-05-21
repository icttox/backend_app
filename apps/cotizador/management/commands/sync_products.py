from django.core.management.base import BaseCommand
from django.db import connections, transaction
from apps.cotizador.models import ProductTemplate, ProductType, ProductFamily, ProductLine, ProductGroup
from datetime import datetime
import logging
from ...cache.sync import sync_products_to_supabase

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza los productos desde la copia de Odoo a la base de datos local'

    def handle(self, *args, **options):
        start_time = datetime.now()
        logger.info(f"Iniciando sincronización de productos: {start_time}")
        
        try:
            # Conectar a la base de datos de Odoo
            with connections['erp-portalgebesa-com'].cursor() as odoo_cursor:
                # Obtener productos de Odoo
                odoo_cursor.execute("""
                    SELECT 
                        pt.id,
                        pt.name,
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
                
                products = odoo_cursor.fetchall()
                
                # Obtener los nombres de las columnas
                columns = [desc[0] for desc in odoo_cursor.description]
                
                # Convertir a diccionarios
                products_data = [dict(zip(columns, product)) for product in products]
                
            # Actualizar la base de datos local en una transacción
            with transaction.atomic():
                # Ya no desactivamos todos los productos, solo actualizamos los que recibimos
                # ProductTemplate.objects.all().update(active=False)
                
                # Lista para registrar productos actualizados
                updated_product_ids = []
                
                # Actualizar o crear productos
                for product in products_data:
                    # Usar name_spanish como name si está disponible, de lo contrario usar name
                    product_name = product.get('name_spanish') if product.get('name_spanish') else product['name']
                    
                    # Usar code como reference_mask
                    reference_mask = product.get('code') or product.get('reference_mask')
                    
                    # Registrar información sobre la traducción y el código
                    if product.get('name_spanish') and product.get('name_spanish') != product['name']:
                        logger.info(f"Usando traducción para ID {product['id']}: '{product['name']}' -> '{product_name}'")
                    
                    if product.get('code') and product.get('code') != product.get('reference_mask'):
                        logger.info(f"Usando código combinado para ID {product['id']}: '{product.get('reference_mask')}' -> '{reference_mask}'")
                    
                    # Verificar si el producto ya existe
                    try:
                        existing_product = ProductTemplate.objects.get(id=product['id'])
                        
                        # Actualizar solo los campos específicos que vienen de Odoo
                        existing_product.name = product_name
                        existing_product.reference_mask = reference_mask
                        existing_product.note_pricelist = product.get('note_pricelist')
                        existing_product.type_id = product['type_id']
                        existing_product.family_id = product['family_id']
                        existing_product.line_id = product['line_id']
                        existing_product.group_id = product['group_id']
                        existing_product.is_line = product['is_line']
                        existing_product.pricelist = product.get('pricelist', False)
                        existing_product.active = product['active']
                        
                        # Guardar los cambios (esto preservará otros campos como URLs de imágenes)
                        existing_product.save()
                        logger.info(f"Producto actualizado: ID {product['id']} - {product_name}")
                    except ProductTemplate.DoesNotExist:
                        # Si el producto no existe, crearlo
                        ProductTemplate.objects.create(
                            id=product['id'],
                            name=product_name,
                            reference_mask=reference_mask,
                            note_pricelist=product.get('note_pricelist'),
                            type_id=product['type_id'],
                            family_id=product['family_id'],
                            line_id=product['line_id'],
                            group_id=product['group_id'],
                            is_line=product['is_line'],
                            pricelist=product.get('pricelist', False),
                            active=product['active'],
                        )
                        logger.info(f"Producto creado: ID {product['id']} - {product_name}")
                    
                    # Registrar este ID como actualizado
                    updated_product_ids.append(product['id'])
                
                # Registrar estadísticas
                total_products = len(products_data)
                active_products = sum(1 for p in products_data if p['active'])
                spanish_names = sum(1 for p in products_data if p.get('name_spanish') and p.get('name_spanish') != p['name'])
                combined_codes = sum(1 for p in products_data if p.get('code') and p.get('code') != p.get('reference_mask'))
                
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"Sincronización completada en {duration}")
            logger.info(f"Total de productos: {total_products}")
            logger.info(f"Productos activos: {active_products}")
            logger.info(f"Productos con nombre en español: {spanish_names}")
            logger.info(f"Productos con código combinado: {combined_codes}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sincronización exitosa. {total_products} productos actualizados en {duration}\n'
                    f'- {active_products} productos activos\n'
                    f'- {spanish_names} productos con nombre en español\n'
                    f'- {combined_codes} productos con código combinado'
                )
            )
            
        except Exception as e:
            logger.error(f"Error durante la sincronización: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error durante la sincronización: {str(e)}')
            )
            raise
