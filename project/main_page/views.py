from django.shortcuts import render
from allauth.account.decorators import verified_email_required

# Create your views here.
@verified_email_required
def home(request):
    # verificar autenticação do usuário
    return render(request, 'main_page/home.html')