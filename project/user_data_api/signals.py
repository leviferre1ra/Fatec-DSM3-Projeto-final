from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.conf import settings
import requests
import logging


logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def create_user_data_via_api(sender, instance=None, created=False, **kwargs):
    if created:
        api_url = f"{settings.API_BASE_URL}/api/user_data/"
        service_token = settings.SERVICE_API_TOKEN
        
        headers = {
            'Authorization': f'Token {service_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'user_id': instance.pk,
            'notifications': [],
            'preferences': {
                "language": "pt-BR",
                "timezone": "America/Sao_Paulo",
                "default_notification_method": "push"
            } 
        }

        try:
            response = requests.post(api_url, headers=headers, json=data)
            
            if response.status_code == 201: # 201 Created é o padrão para POST de sucesso
                logger.info(f"Dados do usuário {instance.pk} criados via API com sucesso.")
            else:
                logger.error(
                    f"Falha ao criar dados do usuário {instance.pk}. Status: {response.status_code}, Resposta: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão ao tentar criar dados do usuário {instance.pk} na API: {e}")

@receiver(post_delete, sender=User)
def delete_user_data_from_api(sender, instance, **kwargs):
    user_id = instance.pk 
    api_url = f"{settings.API_BASE_URL}/api/user_data/{user_id}/"
    service_token = settings.SERVICE_API_TOKEN
    
    headers = {
        'Authorization': f'Token {service_token}'
    }
    
    try:
        response = requests.delete(api_url, headers=headers)
        
        if response.status_code == 204:
            logger.info(f"Dados do usuário {user_id} excluídos com sucesso da API externa.")
        elif response.status_code == 404:
            logger.warning(f"Dados do usuário {user_id} não encontrados na API (404).")
        else:
            logger.error(
                f"Falha ao excluir dados do usuário {user_id}. Status: {response.status_code}, Resposta: {response.text}"
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão ao tentar excluir dados do usuário {user_id} da API: {e}")