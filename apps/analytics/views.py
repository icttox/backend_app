import os
import requests
# Eliminamos la dependencia de dotenv
from django.conf import settings
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import HubspotEngagement
from .serializers import HubspotEngagementSerializer
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model 

User = get_user_model()

# Usando os.environ directamente o settings de Django si están definidos
N8N_WEBHOOK_URL_IA_ANALYTICS = getattr(settings, 'N8N_WEBHOOK_URL_IA_ANALYTICS', os.environ.get('N8N_WEBHOOK_URL_IA_ANALYTICS', ''))
N8N_WEBHOOK_URL_IA_ANALYTICS_TEST = getattr(settings, 'N8N_WEBHOOK_URL_IA_ANALYTICS_TEST', os.environ.get('N8N_WEBHOOK_URL_IA_ANALYTICS_TEST', ''))

class HubspotEngagementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para HubspotEngagement"""
    queryset = HubspotEngagement.objects.all()
    serializer_class = HubspotEngagementSerializer

    @action(detail=False, methods=['get'], url_path='engagements-by-user/(?P<hubspot_id>[^/.]+)')
    def get_engagements_by_user(self, request, hubspot_id = None):
        try:
            engagements = HubspotEngagement.objects.filter(owner_id=hubspot_id)
            serializer = self.get_serializer(engagements, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @action(detail=False, methods=['get'], url_path='dashboard-summary')
    def get_dashboard_summary(self, request):
        try:
            #total de enagagments
            total_engagements_count = HubspotEngagement.objects.count()
            #engagagments_by_type
            engagements_by_type_query = HubspotEngagement.objects.values('type').annotate(count=Count('id')).order_by('-count')
            #engagagments_by_owner Top N, mappeado a nombres de usuario
            top_owners_query = HubspotEngagement.objects.values('owner_id').annotate(count=Count('id')).order_by('-count')[:10]

            owner_ids_for_users = [owner['owner_id'] for owner in top_owners_query if owner['owner_id']]
            
            users_info = User.objects.filter(hubspot_id__in=owner_ids_for_users).values('hubspot_id', 'first_name', 'last_name', 'email')

            user_map = {}
            for user in users_info:
                first_name = user.get('first_name', '')
                last_name_full = user.get('last_name', '')
                email = user.get('email', '')
                
                # Tomar solo el primer apellido
                first_last_name = last_name_full.split(' ')[0] if last_name_full else ''
                
                display_name = f"{first_name} {first_last_name}".strip()
                user_map[str(user['hubspot_id'])] = display_name or email

            engagements_by_owner_list = []
            
            for owner_data in top_owners_query:
                owner_id_str = str(owner_data['owner_id'])
                owner_name = user_map.get(owner_id_str, f"Owner ID: {owner_id_str}") # Fallback si no se encuentra el usuario
                engagements_by_owner_list.append({
                    'owner_name': owner_name,
                    'hubspot_id': owner_id_str, # Incluimos el hubspot_id por si el frontend lo necesita
                    'count': owner_data['count']
                })

            #tendencia de engagaments (ultimos 12 meses)
            engagments_trend_query = HubspotEngagement.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('-month')[:12]

            engagements_trend_list = [{'month': item['month'].strftime('%Y-%m'), 'count': item['count']} for item in engagments_trend_query]
            engagements_trend_list.reverse()


            summary_data = {
                'total_engagements': total_engagements_count,
                'engagements_by_type':list(engagements_by_type_query),
                'engagements_by_owner': engagements_by_owner_list,
                'engagements_trend': engagements_trend_list
            }
            return Response(summary_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

    @action(
        detail=False, 
        methods=['post'], 
        permission_classes=[AllowAny],
        url_path='analysis-ia',
        authentication_classes=[]
    )
    def analysis_ia(self, request):
        try:
            # Obtener la URL del webhook
            webhook_url = N8N_WEBHOOK_URL_IA_ANALYTICS  # Usamos la variable global
            #webhook_url = N8N_WEBHOOK_URL_IA_ANALYTICS_TEST
            
            if not webhook_url:
                print("No se encontró la URL del webhook")
                return Response(
                    {'error': 'Configuración del webhook no encontrada'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            
            
            try:
                response = requests.post(webhook_url, timeout=300)
                
                response.raise_for_status()
                
                try:
                    data = response.json()
                except ValueError as e:
                    print(f"Error al parsear JSON: {str(e)}")
                    return Response(
                        {'error': f'Error al parsear la respuesta del webhook: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Verificar si recibimos datos válidos
                if not data:
                    return Response(
                        {'error': 'El webhook devolvió una respuesta vacía'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
                if not isinstance(data, list):
                    print(f"La respuesta no es una lista: {type(data)}")
                    # Si no es una lista, intentamos convertirla en una lista con un solo elemento
                    data = [data]
                    
                if not data[0]:
                    return Response(
                        {'error': 'El primer elemento de la respuesta está vacío'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                reporte = data[0]  # Obtenemos el primer elemento del array
                
                # Construir el reporte formateado
                reporte_formateado = f"""
📊 *REPORTE SEMANAL DE INTERACCIONES*

📅 *Período analizado*: {reporte['periodoAnalizado']['inicio']} al {reporte['periodoAnalizado']['fin']}

🔍 *Resumen Ejecutivo*
{reporte['resumenEjecutivo']}

📊 *Métricas Clave*
• Total de interacciones: {reporte['totalInteracciones']}
• Día de mayor volumen: {reporte['diaMayorVolumen']['fecha']} ({reporte['diaMayorVolumen']['interacciones']} interacciones)
• Canal principal: {reporte['canalPrincipal']}

📝 *Desglose por tipo de interacción*"""
                
                # Agregar desglose por tipo
                for tipo, cantidad in reporte['desglosePorTipo'].items():
                    porcentaje = (cantidad / reporte['totalInteracciones']) * 100
                    reporte_formateado += f"\n• {tipo}: {cantidad} ({porcentaje:.1f}%)"
                
                # Agregar hallazgos
                reporte_formateado += "\n🔍 *Hallazgos Clave*\n"
                for i, hallazgo in enumerate(reporte['hallazgos'], 1):
                    reporte_formateado += f"{i}. {hallazgo}\n"
                
                # Agregar recomendaciones
                reporte_formateado += "\n💡 *Recomendaciones*\n"
                for i, recomendacion in enumerate(reporte['recomendaciones'], 1):
                    reporte_formateado += f"{i}. {recomendacion}\n"

                print("reporte_formateado", reporte_formateado)
                
                return Response(
                    {'reporte': reporte_formateado},
                    status=status.HTTP_200_OK
                )
                
            except requests.RequestException as e:
                error_msg = f"Error al llamar al webhook: {str(e)}"
                print(error_msg)
                return Response(
                    {'error': error_msg}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            print(error_msg)
            return Response(
                {'error': error_msg}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )