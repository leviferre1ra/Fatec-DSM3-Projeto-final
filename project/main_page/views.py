from django.shortcuts import render
from allauth.account.decorators import login_required

# Create your views here.
@login_required
def home(request):
    # verificar autenticação do usuário
    return render(request, 'main_page/home.html')