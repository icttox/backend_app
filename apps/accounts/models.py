from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from apps.core.constants import (
    AREA_CHOICES,
    TIPO_UNIDAD_CHOICES,
    RAZON_SOCIAL_CHOICES,
    RAZON_SOCIAL_MAPPING,
    RFC_POR_RAZON,
)

class OdooUser(models.Model):
    """
    Modelo para gestionar usuarios de Odoo que pueden ser asignados a unidades
    """
    email = models.EmailField(
        'Email',
        unique=True,
        help_text='Email del usuario de Odoo',
        null=True,
        blank=True
    )
    password = models.CharField(
        max_length=100,
        help_text='Contraseña del usuario de Odoo',
        null=True,
        blank=True
    )
    api_key = models.CharField(
        max_length=100,
        help_text='API Key del usuario de Odoo',
        null=True,
        blank=True
    )
    nombre = models.CharField(
        max_length=100,
        help_text='Nombre descriptivo del usuario de Odoo',
        null=True,
        blank=True
    )
    activo = models.BooleanField(
        default=True,
        help_text='Indica si el usuario de Odoo está activo',
    )

    class Meta: 
        verbose_name = 'Usuario de Odoo'
        verbose_name_plural = 'Usuarios de Odoo'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.email})"

class Unidad(models.Model):
    """
    Modelo para gestionar las unidades/espacios de negocio
    """
    nombre_corto = models.CharField(
        max_length=100,
        unique=True,
        help_text='Nombre corto o comercial de la unidad'
    )
    razon_social = models.CharField(
        max_length=3,
        choices=RAZON_SOCIAL_CHOICES,
        help_text='Razón social de la unidad'
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_UNIDAD_CHOICES,
        help_text='Tipo de unidad (propia, distribuidora, concesionario)'
    )
    nombre_cliente_final = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Nombre del cliente final'
    )
    rfc_cliente_final = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        help_text='RFC del cliente final'
    )
    id_pricelist = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID de la lista de precios para filtrar en el frontend'
    )

    user_api = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        help_text='ID del usuario para consultar clientes por API de odoo'
    )
    
    odoo_user = models.ForeignKey(
        'OdooUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unidades',
        help_text='Usuario de Odoo asignado a esta unidad'
    )

    class Meta:
        verbose_name = 'Unidad'
        verbose_name_plural = 'Unidades'
        ordering = ['nombre_corto']

    def __str__(self):
        return f"{self.nombre_corto} - {self.get_razon_social_display()}"

    @property
    def razon_social_completa(self):
        """Obtiene el nombre completo de la razón social"""
        return RAZON_SOCIAL_MAPPING.get(self.razon_social, '')

    @property
    def rfc_compania(self):
        """Obtiene el RFC de la compañía basado en la razón social"""
        return RFC_POR_RAZON.get(self.razon_social, '')

class UserManager(BaseUserManager):
    def _create_user(self, email, password=None, **extra_fields):
        """
        Método base para crear usuarios.
        Asegura que el email sea obligatorio y normalizado.
        """
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        
        # Generar un username único basado en el email
        username = email.split('@')[0]
        if 'username' not in extra_fields:
            extra_fields['username'] = username
            
        # Asegurarse de que el username sea único
        base_username = username
        counter = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        extra_fields['username'] = username
        
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Crear un usuario regular.
        Por defecto no es staff ni superusuario.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crear un superusuario.
        Debe tener is_staff e is_superuser en True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Modelo de usuario personalizado que coincide con la estructura existente en la base de datos
    """
    username = models.CharField(
        'username',
        max_length=150,
        unique=True,
        help_text='Requerido. 150 caracteres o menos.',
    )
    email = models.EmailField(
        'Email',
        unique=True,
        error_messages={
            'unique': 'Ya existe un usuario con este email.',
        }
    )
    first_name = models.CharField(
        'Nombre',
        max_length=150,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        'Apellido',
        max_length=150,
        blank=True,
        null=True
    )
    phone = models.CharField(
        'Teléfono',
        max_length=15,
        blank=True,
        null=True
    )
    area = models.CharField(
        max_length=20,
        choices=AREA_CHOICES,
        blank=True,
        null=True
    )
    unidad = models.ForeignKey(
        'Unidad',
        on_delete=models.PROTECT,  # No permitir eliminar una unidad si tiene usuarios
        null=True,  # Temporal mientras se migran los datos
        blank=True,
        verbose_name='Unidad',
        help_text='Unidad a la que pertenece el usuario'
    )
    # app de "DATOS"
    hubspot_id = models.CharField(
        'Owner Id de HubSpot',
        max_length=255,
        blank=True,
        null=True,
        help_text='Owner Id de HubSpot del usuario'
    )

    vendedor_id = models.CharField(
        'ID del vendedor en Odoo',
        max_length=50,
        blank=True,
        null=True,
        help_text='ID del vendedor'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email & Password son requeridos por defecto

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        
    def __str__(self):
        return self.email

    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def save(self, *args, **kwargs):
        # Always generate a username from email if not provided
        if not self.username and self.email:
            # Generate a unique username from email
            base_username = self.email.split('@')[0]
            username = base_username
            counter = 1
            # Check for existing usernames, excluding self
            username_exists_query = User.objects.filter(username=username)
            if self.pk:
                username_exists_query = username_exists_query.exclude(pk=self.pk)
                
            while username_exists_query.exists():
                username = f"{base_username}{counter}"
                counter += 1
                username_exists_query = User.objects.filter(username=username)
                if self.pk:
                    username_exists_query = username_exists_query.exclude(pk=self.pk)
                    
            self.username = username
        super().save(*args, **kwargs)

    @property
    def razon_social(self):
        """
        Mantiene compatibilidad con el código existente que use user.razon_social
        """
        if self.unidad:
            return self.unidad.get_razon_social_display()
        return None

    @property
    def rfc_empresa(self):
        """
        Obtiene el RFC de la empresa basado en la unidad
        """
        if self.unidad:
            return self.unidad.rfc_compania
        return None
        
    # Propiedades para acceso directo a los campos del perfil desde el admin
    @property
    def unidades_asignadas(self):
        """Devuelve las unidades asignadas al usuario en su perfil"""
        if hasattr(self, 'profile'):
            return self.profile.unidades_asignadas.all()
        return []
    
    @property
    def nombre_comprador(self):
        """Devuelve el nombre de comprador del usuario en su perfil"""
        if hasattr(self, 'profile'):
            return self.profile.nombre_comprador
        return None
        
    @nombre_comprador.setter
    def nombre_comprador(self, value):
        """Establece el nombre de comprador en el perfil"""
        if hasattr(self, 'profile'):
            self.profile.nombre_comprador = value
            self.profile.save(update_fields=['nombre_comprador'])
    
    @property
    def categorias_compras_asignadas(self):
        """Devuelve las categorías de compras asignadas al usuario en su perfil"""
        if hasattr(self, 'profile'):
            return self.profile.categorias_compras_asignadas.all()
        return []

class UserProfile(models.Model):
    """
    Perfil extendido del usuario para almacenar información adicional
    y gestionar la seguridad.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        null=True,
        default=''
    )
    unidades_asignadas = models.ManyToManyField(
        'Unidad',
        blank=True,
        help_text='Unidades administrativas a las que pertenece el usuario'
    )
    # Relación con las categorías de compras
    categorias_compras_asignadas = models.ManyToManyField(
        'compras.Categoria',
        blank=True,
        related_name='usuarios_asignados',
        help_text='Categorías de productos asignadas a este usuario para compras'
    )
    odoo_user_id = models.IntegerField(
        blank=True,
        null=True,
        help_text='ID de usuario en Odoo para usuarios del área de compras'
    )
    nombre_comprador = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Nombre del comprador que identifica al usuario (si aplica)'
    )
    require_password_change = models.BooleanField(default=True)
    last_password_change = models.DateTimeField(auto_now_add=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    foto = models.ImageField(upload_to='profiles/', blank=True, null=True)

    class Meta:
        verbose_name = _('Perfil de Usuario')
        verbose_name_plural = _('Perfiles de Usuario')

    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"

    def reset_failed_attempts(self):
        """
        Resetea los intentos fallidos de inicio de sesión y desbloquea la cuenta.
        """
        self.user.failed_login_attempts = 0
        self.user.is_locked = False
        self.user.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Señal para crear automáticamente un perfil cuando se crea un usuario.
    """
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(
            user=instance,
            require_password_change=True
        )
