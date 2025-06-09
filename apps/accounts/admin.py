from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm, SelectMultiple
from django import forms
from .models import User, UserProfile, Unidad, OdooUser



class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'
        widgets = {
            'unidades_asignadas': SelectMultiple(attrs={'size': '5', 'class': 'form-control'}),
            'categorias_compras_asignadas': SelectMultiple(attrs={'size': '5', 'class': 'form-control'}),
        }

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    form = UserProfileForm
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'user'
    
    def get_fieldsets(self, request, obj=None):
        # Campos básicos que siempre se muestran
        fieldsets = [
            (_('Información Personal'), {
                'fields': ('avatar', 'bio', 'telefono', 'extension', 'foto')
            }),
            (_('Seguridad'), {
                'fields': ('require_password_change', 'last_password_change')
            }),
        ]
        
        # Agregar fieldsets específicos según el área
        if obj and hasattr(obj, 'area'):
            from apps.core.constants import AREA_COMPRAS, AREA_VENTAS
            
            # Configuración específica para el área de Compras
            if obj.area == AREA_COMPRAS:
                fieldsets.insert(1, (_('Configuración de Compras'), {
                    'fields': ('categorias_compras_asignadas', 'odoo_user_id'),
                    'description': 'Categorías de productos asignadas a este comprador',
                }))
                
            # Configuración específica para el área de Ventas (ejemplo)
            elif obj.area == AREA_VENTAS:
                fieldsets.insert(1, (_('Configuración de Ventas'), {
                    'fields': ('unidades_asignadas',),
                    'description': 'Unidades asignadas para vendedores',
                }))
            
            # Para otras áreas, sin campos específicos adicionales por ahora
            # else:
            #    fieldsets.insert(1, (_('Configuración de [Área]'), {...}))
        
        return fieldsets
    
    readonly_fields = ('last_password_change',)

# Formulario personalizado para crear usuarios
class CustomUserCreationForm(forms.ModelForm):
    """
    Formulario personalizado que acepta directamente el campo 'password'
    en lugar de password1/password2 como lo hace UserCreationForm
    """
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('username', 'email')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que username sea opcional
        if 'username' in self.fields:
            self.fields['username'].required = False
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Establecer la contraseña
        if 'password' in self.cleaned_data:
            user.set_password(self.cleaned_data['password'])
        
        # Generar username si no existe
        if not user.username and user.email:
            base_username = user.email.split('@')[0]
            username = base_username
            counter = 1
            # Verificar que sea único
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username
        
        if commit:
            user.save()
        
        return user

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'hubspot_id', 'get_groups', 'get_unidades', 'get_categorias_compras')
    ordering = ('email',)
    add_form = CustomUserCreationForm
    
    def get_fieldsets(self, request, obj=None):
        # Siempre mostramos estos fieldsets básicos
        fieldsets = [
            (None, {'fields': ('email', 'password')}),
            (_('Información Personal'), {'fields': ('first_name', 'last_name', 'phone')}),
            (_('Información Organizacional'), {
                'fields': ('area','unidad','hubspot_id'),
                'description': 'El área determina qué secciones adicionales estarán disponibles en el perfil del usuario'
            }),
            (_('Permisos'), {
                'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
                'description': 'Se recomienda usar grupos genéricos basados en niveles de responsabilidad (ej. Administrador, BackOffice, Usuario) en lugar de roles específicos por área.',
            }),
            (_('Fechas Importantes'), {'fields': ('last_login', 'date_joined')}),
        ]
        
        return fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo para nuevos usuarios
            if not obj.username and obj.email:
                # Generar username del email
                base_username = obj.email.split('@')[0]
                username = base_username
                counter = 1
                # Asegurar que sea único
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                obj.username = username
        
        super().save_model(request, obj, form, change)

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Grupos'

    def get_unidades(self, obj):
        if hasattr(obj, 'profile'):
            return ", ".join([u.nombre_corto for u in obj.profile.unidades_asignadas.all()])
        return ""
    get_unidades.short_description = 'Unidades'
    
    def get_categorias_compras(self, obj):
        if hasattr(obj, 'profile') and obj.profile.categorias_compras_asignadas.exists():
            return ", ".join([c.nombre for c in obj.profile.categorias_compras_asignadas.all()[:3]])
        return ""
    get_categorias_compras.short_description = 'Categoru00edas de Compras'

class UnidadAdmin(admin.ModelAdmin):
    list_display = ('nombre_corto', 'razon_social', 'get_rfc_display', 'tipo', 'nombre_cliente_final', 'rfc_cliente_final', 'id_pricelist', 'user_api', 'odoo_user')
    list_filter = ('razon_social', 'tipo')
    search_fields = ('nombre_corto', 'nombre_cliente_final', 'rfc_cliente_final', 'rfc_compania')
    ordering = ('nombre_corto',)
    readonly_fields = ('rfc_compania',)

    def get_rfc_display(self, obj):
        return f"{obj.rfc_compania} / {obj.rfc_cliente_final}" if obj.rfc_cliente_final else obj.rfc_compania
    get_rfc_display.short_description = 'RFC (Compañía / Cliente)'
    get_rfc_display.admin_order_field = 'rfc_compania'

class CustomGroupAdmin(GroupAdmin):
    list_display = ('name', 'get_users')
    
    def get_users(self, obj):
        return ", ".join([user.email for user in obj.user_set.all()])
    get_users.short_description = 'Usuarios en el grupo'


class OdooUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'activo', 'id')
    search_fields = ('email', 'nombre')
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Unidad, UnidadAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
admin.site.register(OdooUser, OdooUserAdmin)
