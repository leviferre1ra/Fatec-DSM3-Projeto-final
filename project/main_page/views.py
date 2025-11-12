from django.shortcuts import render
from allauth.account.decorators import login_required
from django.conf import settings
import requests
import json
from datetime import datetime

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
    features = []
    for bairro in bairros_data:
        if 'geometry' in bairro:  # Verifica se tem geometria
            features.append({
                "type": "Feature",
                "properties": {
                    "Bairro": bairro.get('nome', 'Sem nome'),
                    "Dias": bairro.get('dias', []),
                    "Período": bairro.get('periodo', ''),
                    "Horário": bairro.get('horario', '')
                },
                "geometry": bairro['geometry']
            })
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return render(request, 'main_page/home.html', {
        "bairros": bairros_data,
        "geojson": json.dumps(geojson_data),
        "dia_atual": dia_nome
    })