from django.shortcuts import render
from django.http import JsonResponse
from allauth.account.decorators import login_required
from django.conf import settings
import requests
import json
from datetime import datetime
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.utils.decorators import method_decorator

# Create your views here.
@login_required
def home(request):
    # Obter o dia da semana atual
    dias_semana = {
        0: 'segunda',
        1: 'terça',
        2: 'quarta',
        3: 'quinta',
        4: 'sexta',
        5: 'sábado',
        6: 'domingo'
    }
    
    dia_atual = datetime.now().weekday()
    dia_nome = dias_semana[dia_atual]
    
    # Construir URL com o dia da semana
    api_url = f"{settings.API_BASE_URL}/coleta/bairros/?dia={dia_nome}"
    service_token = settings.SERVICE_API_TOKEN

    headers = {
        'Authorization': f'Token {service_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(api_url, headers=headers)
    bairros_data = response.json()
    
    # Converter para GeoJSON FeatureCollection
    geojson_data = converter_para_geojson(bairros_data)
    
    return render(request, 'main_page/home.html', {
        "bairros": bairros_data,
        "geojson": json.dumps(geojson_data),
        "dia_atual": dia_nome
    })

@login_required
def carregar_bairro(request):
    """Endpoint para carregar dados de um bairro específico via AJAX"""
    bairro_selecionado = request.GET.get('bairro', '')
    
    dias_semana = {
        0: 'segunda',
        1: 'terça',
        2: 'quarta',
        3: 'quinta',
        4: 'sexta',
        5: 'sábado',
        6: 'domingo'
    }
    
    dia_atual = datetime.now().weekday()
    dia_nome = dias_semana[dia_atual]
    
    # Construir URL com dia e bairro
    # alterar para: api_url = f"{settings.API_BASE_URL}/coleta/bairros/?dia={dia_nome}&bairro={bairro_selecionado}"
    api_url = f"{settings.API_BASE_URL}/coleta/bairros/?bairro={bairro_selecionado}"
    service_token = settings.SERVICE_API_TOKEN

    headers = {
        'Authorization': f'Token {service_token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(api_url, headers=headers)
        bairros_data = response.json()
        
        # Converter para GeoJSON FeatureCollection
        geojson_data = converter_para_geojson(bairros_data)
        
        return JsonResponse({
            'success': True,
            'geojson': geojson_data,
            'bairros': bairros_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def converter_para_geojson(bairros_data):
    """Função auxiliar para converter dados em GeoJSON"""
    features = []
    for bairro in bairros_data:
        if 'geometry' in bairro:
            features.append({
                "type": "Feature",
                "properties": {
                    "Bairro": bairro.get('properties', {}).get('Bairro', 'Sem nome'),
                    "Dias": bairro.get('properties', {}).get('Dias', []),
                    "Período": bairro.get('properties', {}).get('Período', ''),
                    "Horário": bairro.get('properties', {}).get('Horário', '')
                },
                "geometry": bairro['geometry']
            })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

@require_POST
@login_required
def feedback(request):
    """Recebe feedback via AJAX e envia por email."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    rating = data.get('rating', '')
    email = data.get('email', '')
    message = data.get('message', '')
    subject = f'Feedback — avaliação {rating}'
    body = f'Email: {email}\n\nMensagem:\n{message}'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@exemplo.com')
    to_email = [getattr(settings, 'CONTACT_EMAIL', 'suporte.deolhonolixo@gmail.com')]
    try:
        send_mail(subject, body, from_email, to_email, fail_silently=False)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': True})