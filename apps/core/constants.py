"""
Constantes globales para la aplicación
"""

# Roles de usuario
ROL_SUPERUSUARIO = 'SUPER'
ROL_GERENTE = 'GERENTE'
ROL_LIDER = 'LIDER'
ROL_VENDEDOR = 'VENDEDOR'
ROL_BACKOFFICE = 'BACKOFFICE'

ROL_CHOICES = [
    (ROL_SUPERUSUARIO, 'Superusuario'),
    (ROL_GERENTE, 'Gerente de Ventas'),
    (ROL_LIDER, 'Líder de Sucursal'),
    (ROL_VENDEDOR, 'Vendedor'),
    (ROL_BACKOFFICE, 'Backoffice'),
]

# Áreas
AREA_RH = 'RH'
AREA_VENTAS = 'VENTAS'
AREA_COMPRAS = 'COMPRAS'
AREA_PRODUCCION = 'PROD'
AREA_TI = 'TI'
AREA_AIP = 'AIP'

AREA_CHOICES = [
    (AREA_RH, 'Recursos Humanos'),
    (AREA_VENTAS, 'Ventas'),
    (AREA_COMPRAS, 'Compras'),
    (AREA_PRODUCCION, 'Producción'),
    (AREA_TI, 'Tecnología'),
    (AREA_AIP, 'AIP'),
]

# Tipos de unidad
TIPO_PROPIA = 'PROPIA'
TIPO_DISTRIBUIDORA = 'DISTRIBUIDORA'
TIPO_CONCESIONARIO = 'CONCESIONARIO'

TIPO_UNIDAD_CHOICES = [
    (TIPO_PROPIA, 'Propia'),
    (TIPO_DISTRIBUIDORA, 'Distribuidora'),
    (TIPO_CONCESIONARIO, 'Concesionario'),
]

# Razones sociales
RAZON_MPF = 'MPF'  # Manufacturas Post Form
RAZON_SLL = 'SLL'  # Salmon De La Laguna
RAZON_OSG = 'OSG'  # Operadora de Sucursales Gebesa
RAZON_GNA = 'GNA'  # GEBESA NACIONAL

# Mapeo de razones sociales completas
RAZON_SOCIAL_MAPPING = {
    RAZON_MPF: 'MANUFACTURAS POST FORM',
    RAZON_SLL: 'Salmon De La Laguna S.A. de C.V.',
    RAZON_OSG: 'Operadora de Sucursales Gebesa S.A. de C.V.',
    RAZON_GNA: 'GEBESA NACIONAL',
}

RAZON_SOCIAL_CHOICES = [(k, v) for k, v in RAZON_SOCIAL_MAPPING.items()]

# Mapeo de códigos RFC por razón social
RFC_POR_RAZON = {
    RAZON_MPF: 'MPF861014CD6',
    RAZON_SLL: 'SLA8210184A7',
    RAZON_OSG: 'OSG161026F56',
    RAZON_GNA: 'GNA120703RV1',
}

# Datos iniciales de unidades
UNIDADES_INICIALES = [
    {
        "nombre_corto": "Monterrey",
        "razon_social": RAZON_GNA,
        "tipo": TIPO_PROPIA,
        "nombre_cliente_final": "Cotización",
        "rfc_cliente_final": "Cotización"
    },
    {
        "nombre_corto": "CDMX",
        "razon_social": RAZON_GNA,
        "tipo": TIPO_PROPIA,
        "nombre_cliente_final": "Cotización",
        "rfc_cliente_final": "Cotización"
    },
    {
        "nombre_corto": "Puebla",
        "razon_social": RAZON_OSG,
        "tipo": TIPO_PROPIA,
        "nombre_cliente_final": "Cotización",
        "rfc_cliente_final": "Cotización"
    },
    {
        "nombre_corto": "Laguna",
        "razon_social": RAZON_SLL,
        "tipo": TIPO_PROPIA,
        "nombre_cliente_final": "Cotización",
        "rfc_cliente_final": "Cotización"
    },
    {
        "nombre_corto": "Querétaro",
        "razon_social": RAZON_OSG,
        "tipo": TIPO_PROPIA,
        "nombre_cliente_final": "Cotización",
        "rfc_cliente_final": "Cotización"
    },
    {
        "nombre_corto": "Guadalajara",
        "razon_social": RAZON_OSG,
        "tipo": TIPO_PROPIA,
        "nombre_cliente_final": "Cotización",
        "rfc_cliente_final": "Cotización"
    },
    {
        "nombre_corto": "Metrópoli",
        "razon_social": RAZON_MPF,
        "tipo": TIPO_PROPIA,
        "nombre_cliente_final": "Gebesa Metropoli S.A. de C.V.",
        "rfc_cliente_final": "GME020523DP7"
    },
    {
        "nombre_corto": "Mérida",
        "razon_social": RAZON_MPF,
        "tipo": TIPO_DISTRIBUIDORA,
        "nombre_cliente_final": "FUSION DE NEGOCIOS SA DE CV",
        "rfc_cliente_final": "FNE1011056K1"
    },
    {
        "nombre_corto": "León",
        "razon_social": RAZON_MPF,
        "tipo": TIPO_CONCESIONARIO,
        "nombre_cliente_final": "PROVEDURIA DE SERVICIOS Y PRODUCTOS DE MEXICO SA DE CV",
        "rfc_cliente_final": "PPS090331MD3"
    },
    {
        "nombre_corto": "Tijuana",
        "razon_social": RAZON_MPF,
        "tipo": TIPO_CONCESIONARIO,
        "nombre_cliente_final": "ESPACIOS E IMAGEN DE OFICINA SA DE CV",
        "rfc_cliente_final": "EEI110611UI3"
    },
    {
        "nombre_corto": "Hermosillo",
        "razon_social": RAZON_MPF,
        "tipo": TIPO_CONCESIONARIO,
        "nombre_cliente_final": "ESPACIOS E IMAGEN DE OFICINA SA DE CV",
        "rfc_cliente_final": "EEI110611UI3"
    },
    {
        "nombre_corto": "Chihuahua",
        "razon_social": RAZON_MPF,
        "tipo": TIPO_CONCESIONARIO,
        "nombre_cliente_final": "OFICASA SA DE CV",
        "rfc_cliente_final": "OFI850703E75"
    }
]
