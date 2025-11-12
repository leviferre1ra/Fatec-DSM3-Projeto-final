from django.apps import AppConfig


class CityDataApiConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'city_data_api'
