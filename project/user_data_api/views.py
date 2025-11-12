from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status
from .serializers import (
    UserDataSerializer,
    NotificationSerializer,
    AddressUpdateSerializer, 
    TriggerUpdateSerializer, 
    NotificationTypeUpdateSerializer, 
    ScheduleUpdateSerializer
)
from .permissions import IsOwnerOrReadOnly
from .models import UserData
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid


class UserDataViewSet(viewsets.ModelViewSet):
    serializer_class = UserDataSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    queryset = UserData.objects.all() 
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_authenticated and user.is_superuser:
            return UserData.objects.all()
        
        return UserData.objects.filter(user_id=user.pk)


class NotificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_user_data_object(self, user_id_from_url):
        return get_object_or_404(UserData, user_id=user_id_from_url)

    # GET /api/user_data/{user_id}/notifications/
    def list(self, request, user_pk=None):
        user_data = self.get_user_data_object(user_pk)
        
        self.check_object_permissions(request, user_data) 
        
        serializer = NotificationSerializer(user_data.notifications, many=True)
        return Response(serializer.data)

    # POST /api/user_data/{user_id}/notifications/
    def create(self, request, user_pk=None):
        user_data = self.get_user_data_object(user_pk) 
        self.check_object_permissions(request, user_data)
        
        serializer = NotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            new_notification = serializer.validated_data
            new_notification['alert_id'] = str(uuid.uuid4())[:8] 
            new_notification['created_at'] = timezone.now().isoformat()

            user_data.notifications.append(new_notification)
            user_data.save() 
            
            return Response(new_notification, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    # DELETE /api/user_data/{user_id}/notifications/{alert_id}/
    def destroy(self, request, pk=None):
        user_data = self.get_user_data_object(request.user.pk)
        
        initial_count = len(user_data.notifications)
        user_data.notifications = [
            n for n in user_data.notifications if n.get('alert_id') != pk
        ]
        
        if len(user_data.notifications) < initial_count:
            user_data.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response({'detail': 'Notificação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Método auxiliar para buscar uma notificação específica dentro do UserData
    def _get_notification_and_user_data(self, user_pk, alert_id):
        user_data = self.get_user_data_object(user_pk)

        self.check_object_permissions(self.request, user_data) 
        
        try:
            index = next(
                i for i, n in enumerate(user_data.notifications) 
                if n.get('alert_id') == alert_id
            )
            return user_data, user_data.notifications[index], index
        except StopIteration:
            return None, None, -1

    # Método genérico para atualizar um sub-campo
    def _update_sub_field(self, user_pk, alert_id, sub_field_name, serializer_class):
        user_data, notification, index = self._get_notification_and_user_data(user_pk, alert_id)

        if not notification:
            return Response({'detail': 'Notificação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_class(
            data=self.request.data, 
            instance=notification.get(sub_field_name), 
            partial=True
        )
        
        if serializer.is_valid():
            updated_data = {**notification.get(sub_field_name, {}), **serializer.validated_data}
            
            user_data.notifications[index][sub_field_name] = updated_data
            user_data.save()
            
            return Response(updated_data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # PATCH /api/user_data/{user_id}/notifications/{alert_id}/address/
    def update_address(self, request, user_pk=None, pk=None):
        return self._update_sub_field(user_pk, pk, 'address', AddressUpdateSerializer)

    # PATCH /api/user_data/{user_id}/notifications/{alert_id}/trigger/
    def update_trigger(self, request, user_pk=None, pk=None):
        return self._update_sub_field(user_pk, pk, 'trigger', TriggerUpdateSerializer)

    # PATCH /api/user_data/{user_id}/notifications/{alert_id}/notification_type/
    def update_notification_type(self, request, user_pk=None, pk=None):
        return self._update_sub_field(user_pk, pk, 'notification', NotificationTypeUpdateSerializer)

    # PATCH /api/user_data/{user_id}/notifications/{alert_id}/schedule/
    def update_schedule(self, request, user_pk=None, pk=None):
        return self._update_sub_field(user_pk, pk, 'schedule', ScheduleUpdateSerializer)

    # PATCH /api/user_data/{user_id}/notifications/{alert_id}/active/
    def update_active_status(self, request, user_pk=None, pk=None):
        user_data, notification, index = self._get_notification_and_user_data(user_pk, pk)

        if not notification:
            return Response({'detail': 'Notificação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('active')
        
        if is_active is None or not isinstance(is_active, bool):
             return Response({'active': ['Este campo é obrigatório e deve ser booleano.']}, status=status.HTTP_400_BAD_REQUEST)

        user_data.notifications[index]['active'] = is_active
        user_data.save()
        
        return Response({'active': is_active}, status=status.HTTP_200_OK)