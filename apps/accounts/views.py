from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, Unidad
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    ChangePasswordSerializer,
    UnidadSerializer,
    GroupSerializer
)
from apps.core.permissions import IsAdminUser, IsOwnerOrAdmin, HasAreaPermission, RequirePasswordChange
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q

User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Por favor proporcione email y contraseña'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data
            
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data,
            })
        else:
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Sesión cerrada correctamente'})
        except Exception:
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)

class VerifyAccessView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({'message': 'Token válido'})

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios.
    Implementa RBAC (Role-Based Access Control) donde:
    - Administradores pueden crear, listar y eliminar usuarios
    - Gerentes de Ventas pueden ver y modificar usuarios en todas las unidades
    - Líderes de Sucursal pueden ver y modificar usuarios de su unidad
    - Vendedores solo pueden ver y modificar su propia información
    - Backoffice puede ver información de usuarios
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all().select_related('profile').prefetch_related('groups')
        
        # Administrador: acceso total
        if user.groups.filter(name='Administrador').exists():
            return queryset
            
        # Gerente de Ventas: acceso a todos los usuarios
        if user.groups.filter(name='Gerente de Ventas').exists():
            return queryset
            
        # Líder de Sucursal: acceso a usuarios de su unidad
        if user.groups.filter(name='Líder de Sucursal').exists():
            return queryset.filter(profile__unidad=user.profile.unidad)
            
        # Backoffice: solo lectura de todos los usuarios
        if user.groups.filter(name='Backoffice').exists():
            return queryset
            
        # Vendedor: solo acceso a su propio usuario
        return queryset.filter(id=user.id)

    def get_permissions(self):
        """
        Define permisos según la acción y el rol del usuario
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Al crear un usuario, registrar quién lo creó y su IP.
        """
        user = serializer.save()
        # Registrar la IP del creador si está autenticado
        if self.request.user.is_authenticated:
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            # Aquí podrías guardar la IP en algún lugar si lo necesitas

    @action(detail=False, methods=['post'])
    def check_email(self, request):
        """
        Endpoint público para verificar si un email ya está registrado.
        """
        email = request.data.get('email', '')
        exists = User.objects.filter(email=email).exists()
        return Response({'exists': exists})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Endpoint para obtener el perfil del usuario actual
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available_groups(self, request):
        """
        Devuelve los grupos disponibles para asignar a usuarios
        """
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        """
        Permite a un usuario cambiar su propia contraseña.
        Requiere la contraseña actual y la nueva contraseña.
        """
        user = self.get_object()
        if user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "No tienes permiso para cambiar la contraseña de otro usuario"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": "Contraseña actual incorrecta"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response({"status": "Contraseña actualizada correctamente"})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Permite a los administradores activar una cuenta de usuario.
        """
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"message": "Usuario activado correctamente"})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Permite a los administradores desactivar una cuenta de usuario.
        """
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({"message": "Usuario desactivado correctamente"})

class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar grupos (roles)
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        return Group.objects.all().order_by('name')

    @action(detail=True, methods=['post'])
    def add_permissions(self, request, pk=None):
        group = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.add(*permissions)
        return Response({'status': 'permissions added'})

    @action(detail=True, methods=['post'])
    def remove_permissions(self, request, pk=None):
        group = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.remove(*permissions)
        return Response({'status': 'permissions removed'})

class UnidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar unidades.
    Implementa RBAC donde:
    - Administradores tienen acceso total
    - Gerentes de Ventas pueden ver y modificar todas las unidades
    - Líderes de Sucursal pueden ver y modificar su unidad
    - Vendedores pueden ver su unidad
    - Backoffice puede ver todas las unidades
    """
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Unidad.objects.all()
        
        # Administrador y Gerente de Ventas: acceso total
        if user.groups.filter(name__in=['Administrador', 'Gerente de Ventas']).exists():
            return queryset
            
        # Líder de Sucursal y Vendedor: solo su unidad
        if user.groups.filter(name__in=['Líder de Sucursal', 'Vendedor']).exists():
            return queryset.filter(id=user.profile.unidad.id)
            
        # Backoffice: ver todas las unidades
        if user.groups.filter(name='Backoffice').exists():
            return queryset
            
        return Unidad.objects.none()
    
    def get_permissions(self):
        """
        Define permisos según la acción y el rol del usuario
        """
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, HasAreaPermission]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Permite filtrar unidades por varios parámetros
        """
        queryset = Unidad.objects.all()
        
        # Filtrar por razón social
        razon_social = self.request.query_params.get('razon_social', None)
        if razon_social:
            queryset = queryset.filter(razon_social=razon_social)
            
        # Filtrar por tipo
        tipo = self.request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
            
        # Búsqueda por nombre o RFC
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nombre_corto__icontains=search) |
                Q(nombre_cliente_final__icontains=search) |
                Q(rfc_compania__icontains=search) |
                Q(rfc_cliente_final__icontains=search)
            )
            
        return queryset.order_by('nombre_corto')

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """
        Devuelve las opciones disponibles para los campos de selección
        """
        return Response({
            'razon_social_choices': dict(Unidad.RAZON_SOCIAL_CHOICES),
            'tipo_choices': dict(Unidad.TIPO_CHOICES)
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Devuelve solo las unidades activas
        """
        unidades = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(unidades, many=True)
        return Response(serializer.data)

class QuotationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Endpoint para verificar acceso al cotizador
        """
        return Response({
            'message': 'Acceso permitido al cotizador',
            'user': {
                'name': f"{request.user.first_name} {request.user.last_name}",
                'area': request.user.area,
                'email': request.user.email
            }
        })

    def post(self, request):
        """
        Endpoint para simular la creación de una cotización
        """
        if request.user.area != 'VENTAS':
            return Response({
                'error': 'Solo el personal de ventas puede crear cotizaciones'
            }, status=status.HTTP_403_FORBIDDEN)

        # Aquí iría la lógica real del cotizador
        return Response({
            'message': 'Cotización creada exitosamente',
            'quotation_data': {
                'created_by': request.user.email,
                'created_at': timezone.now(),
                'status': 'pending'
            }
        })

class LoginAPIView(LoginView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                'message': 'Has iniciado sesión correctamente.'
            })
        else:
            return Response({
                'error': 'Usuario o contraseña incorrectos.'
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(LogoutView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({
            'message': 'Has cerrado sesión correctamente.'
        })