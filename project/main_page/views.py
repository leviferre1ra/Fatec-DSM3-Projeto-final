from django.shortcuts import render
from allauth.account.decorators import login_required
from django.conf import settings
import requests

# Create your views here.
@login_required
def home(request):
    # verificar autenticação do usuário
    api_url = f"{settings.API_BASE_URL}/coleta/bairros/"
    service_token = settings.SERVICE_API_TOKEN

    headers = {
        'Authorization': f'Token {service_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(api_url, headers=headers)
    return render(request, 'main_page/home.html')