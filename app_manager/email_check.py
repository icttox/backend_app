from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

User = get_user_model()

class CheckEmailAPIView(APIView):
    """
    Vista independiente para verificar si un email ya está registrado en el sistema.
    No requiere autenticación ni tokens.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '')
        if not email:
            return Response({
                'error': 'Se requiere un email para verificar'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(email=email).exists()
        return Response({'exists': exists})
