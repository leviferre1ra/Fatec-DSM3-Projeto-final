from rest_framework import serializers
from .models import Bairro

class BairroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bairro
        fields = ['type', 'properties', 'geometry']