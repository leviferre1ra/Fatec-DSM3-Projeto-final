from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/carregar-bairro/', views.carregar_bairro, name='carregar_bairro'),
    path('feedback/', views.feedback, name='feedback'),
]