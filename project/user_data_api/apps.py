from django.apps import AppConfig


class UserDataApiConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'user_data_api'

    def ready(self):
        # Importa o arquivo signals para conectar os handlers
        import user_data_api.signals
