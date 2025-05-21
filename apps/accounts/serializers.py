from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import UserProfile, Unidad, OdooUser

User = get_user_model()

class OdooUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdooUser
        fields = ('nombre', 'email')
    

class UnidadSerializer(serializers.ModelSerializer):
    razon_social_display = serializers.CharField(source='get_razon_social_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    rfc_compania = serializers.CharField(read_only=True)
    rfc_cliente_final = serializers.CharField()
    
    class Meta:
        model = Unidad
        fields = (
            'id', 
            'nombre_corto', 
            'razon_social',
            'razon_social_display',
            'rfc_compania',
            'rfc_cliente_final',
            'tipo',
            'tipo_display',
            'nombre_cliente_final',
            'id_pricelist',
            'user_api'
        )

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')

    def create(self, validated_data):
        return Group.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    unidades_asignadas = UnidadSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'avatar', 
            'bio', 
            'require_password_change',
            'unidades_asignadas',
            'telefono',
            'extension',
            'foto'
        )
        read_only_fields = ('require_password_change',)

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    unidad_details = UnidadSerializer(source='unidad', read_only=True)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    groups = GroupSerializer(many=True, required=False, read_only=True)
    group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = (
            'id', 
            'email',
            'username', 
            'password', 
            'first_name', 
            'last_name', 
            'phone', 
            'area',
            'unidad',
            'unidad_details', 
            'is_active',
            'is_staff',
            'groups',
            'group_ids',
            'profile', 
            'date_joined'
        )
        read_only_fields = ('date_joined', 'is_active')

    def create(self, validated_data):
        if not self.context.get('request').method == 'POST':
            return super().create(validated_data)

        if 'email' not in validated_data:
            raise serializers.ValidationError({'email': 'Este campo es requerido para crear un usuario'})
        if 'password' not in validated_data:
            raise serializers.ValidationError({'password': 'Este campo es requerido para crear un usuario'})

        # Manejar grupos
        group_ids = validated_data.pop('group_ids', [])
        
        # Generar username si no se proporciona
        if 'username' not in validated_data:
            email_username = validated_data['email'].split('@')[0]
            base_username = email_username
            counter = 1
            username = base_username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            validated_data['username'] = username

        # Crear usuario
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        
        # Asignar grupos
        if group_ids:
            user.groups.set(Group.objects.filter(id__in=group_ids))
        
        return user

    def update(self, instance, validated_data):
        # Manejar grupos en actualización
        group_ids = validated_data.pop('group_ids', None)
        if group_ids is not None:
            instance.groups.set(Group.objects.filter(id__in=group_ids))
            
        # Remover password si está presente
        validated_data.pop('password', None)
        return super().update(instance, validated_data)

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña por el propio usuario
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data
