from django.db import models
from django.contrib.auth import get_user_model


class UserData(models.Model):
    user_id = models.OneToOneField(
        get_user_model(), 
        on_delete=models.DO_NOTHING,
        primary_key=True,
        db_constraint=False
    )
    
    notifications = models.JSONField(
        default=list, 
        blank=True, 
        help_text='Lista de alertas de notificação aninhados.'
    )
    
    def get_default_preferences():
        return {
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo",
            "default_notification_method": "push"
        }

    preferences = models.JSONField(
        default=get_default_preferences,
        help_text='Preferências do usuário, como idioma e fuso horário.'
    )

    class Meta:
        verbose_name = "Dados do Usuário (MongoDB)"
        verbose_name_plural = "Dados dos Usuários (MongoDB)"

    def __str__(self):
        return f"Dados de Notificação para {self.user_id.username}"