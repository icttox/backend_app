from rest_framework import permissions

# Roles para la app de cotizaciones
ROLE_ADMINISTRADOR = 'Administrador'
ROLE_MANAGER = 'Manager'
ROLE_VENDEDOR = 'Vendedor'
ROLE_BACKOFFICE = 'Backoffice'
ROLE_MARKETING = 'Marketing'

# Áreas permitidas
AREA_RH = 'RH'
AREA_VENTAS = 'VENTAS'
AREA_COMPRAS = 'COMPRAS'
AREA_PRODUCCION = 'PROD'
AREA_TI = 'TI'

AREAS_PERMITIDAS = [
    AREA_RH,
    AREA_VENTAS,
    AREA_COMPRAS,
    AREA_PRODUCCION,
    AREA_TI
]

# Unidades administrativas (IDs)
UNIDAD_MTY = 32  # Monterrey
UNIDAD_SPL = 33  # SPL
UNIDAD_QRO = 34  # Querétaro
UNIDAD_LAG = 40  # Laguna
UNIDAD_CDMX = 43  # CDMX, Puebla, GDL

# Unidades de descuento (códigos)
UNIDAD_DESC_CDMX = 'CDMX'
UNIDAD_DESC_QRO = 'QRO'
UNIDAD_DESC_LAG = 'LAG'
UNIDAD_DESC_MTY = 'MTY'
UNIDAD_DESC_SPL = 'SPL'
UNIDAD_DESC_GDL = 'GDL'
UNIDAD_DESC_PUE = 'PUE'

# Nombres de unidades administrativas para display
UNIDAD_NOMBRES = {
    UNIDAD_MTY: 'Monterrey',
    UNIDAD_SPL: 'SPL',
    UNIDAD_QRO: 'Querétaro',
    UNIDAD_LAG: 'Laguna',
    UNIDAD_CDMX: 'CDMX'
}

# Lista de unidades administrativas
UNIDADES_NEGOCIO = list(UNIDAD_NOMBRES.keys())

# Lista de unidades de descuento
UNIDADES_DESCUENTO = [
    UNIDAD_DESC_CDMX,
    UNIDAD_DESC_QRO,
    UNIDAD_DESC_LAG,
    UNIDAD_DESC_MTY,
    UNIDAD_DESC_SPL,
    UNIDAD_DESC_GDL,
    UNIDAD_DESC_PUE
]

# Razones sociales
RAZON_GEBESA = 'GEBESA_NACIONAL'
RAZON_OPERADORA = 'OPERADORA_SUCURSALES'
RAZON_SALMON = 'SALMON_LAGUNA'

RAZONES_SOCIALES = [
    RAZON_GEBESA,
    RAZON_OPERADORA,
    RAZON_SALMON
]

# Mapeo de unidades administrativas a razones sociales permitidas
UNIDAD_RAZON_SOCIAL_MAPPING = {
    UNIDAD_CDMX: [RAZON_GEBESA, RAZON_OPERADORA],
    UNIDAD_QRO: [RAZON_GEBESA, RAZON_OPERADORA],
    UNIDAD_LAG: [RAZON_SALMON],
    UNIDAD_MTY: [RAZON_GEBESA, RAZON_OPERADORA],
    UNIDAD_SPL: [RAZON_GEBESA]
}

#Funcion para obtener el rol del usuario
def get_cotizador_rol(user):
    if user.is_superuser:
        return ROLE_ADMINISTRADOR
    
    #obtenemos los nombres de los grupos al que pertenece el usuario
    user_groups = list(user.groups.values_list('name', flat=True))

    #Asumimos que cada usuario tiene unicamente un rol
    if ROLE_MANAGER in user_groups:
        return ROLE_MANAGER
    elif ROLE_BACKOFFICE in user_groups:
        return ROLE_BACKOFFICE
    elif ROLE_VENDEDOR in user_groups:
        return ROLE_VENDEDOR
    elif ROLE_MARKETING in user_groups:
        return ROLE_MARKETING

    return None

def validate_unidad_razon_social(user):
    """
    Valida que la razón social del usuario corresponda con su unidad
    """
    if user.is_superuser:
        return True
        
    if user.unidad not in UNIDAD_RAZON_SOCIAL_MAPPING:
        return False
        
    return user.razon_social in UNIDAD_RAZON_SOCIAL_MAPPING[user.unidad]

def can_create_cotizacion(user):
    """
    Verifica si un usuario puede crear cotizaciones:
    - Debe tener rol Manager o Vendedor
    - Su razón social debe corresponder con su unidad
    - Debe pertenecer al área de ventas
    """
    if not validate_unidad_razon_social(user):
        return False
        
    if user.area != AREA_VENTAS:
        return False
        
    role = get_cotizador_rol(user)
    return role in [ROLE_MANAGER, ROLE_VENDEDOR]

def can_view_cotizaciones(user, cotizacion_owner=None):
    """
    Verifica permisos para ver cotizaciones:
    - Manager y Backoffice ven todas las cotizaciones
    - Vendedores solo ven sus propias cotizaciones
    - Debe pertenecer al área de ventas
    """
    if not validate_unidad_razon_social(user):
        return False
        
    if user.area != AREA_VENTAS:
        return False
        
    role = get_cotizador_rol(user)
    if role in [ROLE_MANAGER, ROLE_BACKOFFICE, ROLE_ADMINISTRADOR]:
        return True
    elif role == ROLE_VENDEDOR:
        return cotizacion_owner == user
    return False

def can_view_cotizacion_by_unidad(user, cotizacion):
    """
    Verifica si un usuario puede ver una cotización específica:
    - Administradores pueden ver todo
    - Managers pueden ver todas las cotizaciones
    - Vendedores solo ven sus propias cotizaciones
    """
    if not validate_unidad_razon_social(user):
        return False
        
    role = get_cotizador_rol(user)
    
    if role in [ROLE_ADMINISTRADOR, ROLE_MANAGER]:
        return True
    
    # Validar que la razón social coincida
    if cotizacion.unidad_facturacion != user.razon_social:
        return False
    
    if role == ROLE_VENDEDOR:
        return cotizacion.created_by == user
    
    return False

def can_edit_cotizacion(user, cotizacion):
    """
    Verifica permisos para editar cotizaciones:
    - Administradores pueden editar todo
    - Managers pueden editar cualquier cotización
    - Backoffice solo puede editar de su unidad/razón social
    """
    if not validate_unidad_razon_social(user):
        return False
        
    role = get_cotizador_rol(user)
    
    # Admins y Managers pueden editar todo
    if role in [ROLE_ADMINISTRADOR, ROLE_MANAGER]:
        return True
        
    if role == ROLE_BACKOFFICE:
        # Backoffice solo puede editar de su unidad/razón social
        return (cotizacion.created_by.unidad == user.unidad and
                cotizacion.unidad_facturacion == user.razon_social)
    
    return False

class CotizadorPermission(permissions.BasePermission):
    """
    Permisos personalizados para el módulo de cotizaciones:
    - Validación por rol
    - Validación por unidad
    - Validación por razón social
    - Validación por área
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        role = get_cotizador_rol(request.user)
        if not role:
            return False

        if request.method == 'POST':
            return can_create_cotizacion(request.user)
        
        return can_view_cotizaciones(request.user)
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return can_edit_cotizacion(request.user, obj)
        
        return can_view_cotizacion_by_unidad(request.user, obj)

class IsAdminUser(permissions.BasePermission):
    """
    Permite acceso solo a usuarios administradores.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permite acceso al propietario del objeto o a administradores.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.id == request.user.id

class HasAreaPermission(permissions.BasePermission):
    """
    Permite acceso basado en el área del usuario.
    """
    def __init__(self, allowed_areas):
        self.allowed_areas = allowed_areas

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.area in self.allowed_areas
        )

class RequirePasswordChange(permissions.BasePermission):
    """
    Restringe el acceso si el usuario necesita cambiar su contraseña.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Permitir acceso a la vista de cambio de contraseña
        if view.__class__.__name__ == 'ChangePasswordView':
            return True
            
        # Verificar si el usuario necesita cambiar su contraseña
        try:
            return not request.user.profile.require_password_change
        except:
            return True
