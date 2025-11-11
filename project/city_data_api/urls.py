from django.urls import path
from .views import BairrosAPIView

urlpatterns = [
    path("bairros/", BairrosAPIView.as_view(), name="bairros-list"),
]