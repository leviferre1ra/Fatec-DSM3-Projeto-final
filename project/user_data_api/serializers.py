from rest_framework import serializers
from .models import UserData

class UserDataSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = UserData
        fields = '__all__'

class AddressSerializer(serializers.Serializer):
    street = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=10)
    neighborhood = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=2)

class TriggerSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['time', 'location'])
    value = serializers.IntegerField(required=False)
    units = serializers.ChoiceField(choices=['minutes', 'meters'], required=False)

class NotificationTypeSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['push', 'email', 'sms'])
    title = serializers.CharField(max_length=100)

class ScheduleSerializer(serializers.Serializer):
    days = serializers.ListField(
        child=serializers.CharField(max_length=16),
        min_length=1
    )
    time = serializers.CharField(max_length=5) 
    
    def validate_time(self, value):
        from datetime import time
        import re
        
        # Opcional: Validação de formato (HH:MM)
        if not re.match(r'^\d{2}:\d{2}$', value):
            raise serializers.ValidationError("O campo 'time' deve estar no formato 'HH:MM'.")
            
        try:
            # Tenta converter para Time para garantir que o valor seja válido,
            # mas retorna a string original para salvar no MongoDB.
            time.fromisoformat(value)
        except ValueError:
            raise serializers.ValidationError("O campo 'time' não é um horário válido.")
            
        return value # Retorna a string, não o objeto time!

class NotificationSerializer(serializers.Serializer):
    alert_id = serializers.CharField(read_only=True) 
    created_at = serializers.DateTimeField(read_only=True)
    
    address = AddressSerializer()
    trigger = TriggerSerializer()
    notification = NotificationTypeSerializer()
    schedule = ScheduleSerializer()
    
    active = serializers.BooleanField(default=True)

# --- 1. Serializer para atualizar apenas o endereço ---
class AddressUpdateSerializer(serializers.Serializer):
    # Todos os campos são opcionais para o PATCH
    street = serializers.CharField(max_length=255, required=False)
    number = serializers.CharField(max_length=10, required=False)
    neighborhood = serializers.CharField(max_length=100, required=False)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=2, required=False)

# --- 2. Serializer para atualizar apenas o trigger ---
class TriggerUpdateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['time', 'location'], required=False)
    value = serializers.IntegerField(required=False)
    units = serializers.ChoiceField(choices=['minutes', 'meters'], required=False)

# --- 3. Serializer para atualizar apenas a notificação (método/título) ---
class NotificationTypeUpdateSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['push', 'email', 'sms'], required=False)
    title = serializers.CharField(max_length=100, required=False)

# --- 4. Serializer para atualizar apenas o schedule ---
class ScheduleUpdateSerializer(serializers.Serializer):
    days = serializers.ListField(
        child=serializers.CharField(max_length=16),
        min_length=1,
        required=False
    )
    # Mantemos como CharField para evitar o erro de serialização do MongoDB (datetime.time)
    time = serializers.CharField(max_length=5, required=False)