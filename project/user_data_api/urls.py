from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user_data_api.views import UserDataViewSet
from user_data_api.views import NotificationViewSet

router = DefaultRouter()
router.register(r'user_data', UserDataViewSet)

urlpatterns = [
    path('user_data/<int:user_pk>/notifications/', 
         NotificationViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='user-notification-list'),

    path('user_data/<int:user_pk>/notifications/<str:pk>/', 
         NotificationViewSet.as_view({'delete': 'destroy'}), 
         name='user-notification-detail'),

    path('user_data/<int:user_pk>/notifications/<str:pk>/address/',
         NotificationViewSet.as_view({'patch': 'update_address'}),
         name='notification-patch-address'),
         
    path('user_data/<int:user_pk>/notifications/<str:pk>/trigger/',
         NotificationViewSet.as_view({'patch': 'update_trigger'}),
         name='notification-patch-trigger'),

    path('user_data/<int:user_pk>/notifications/<str:pk>/notification_type/',
         NotificationViewSet.as_view({'patch': 'update_notification_type'}),
         name='notification-patch-notification-type'),

    path('user_data/<int:user_pk>/notifications/<str:pk>/schedule/',
         NotificationViewSet.as_view({'patch': 'update_schedule'}),
         name='notification-patch-schedule'),

    path('user_data/<int:user_pk>/notifications/<str:pk>/active/',
         NotificationViewSet.as_view({'patch': 'update_active_status'}),
         name='notification-patch-active-status'),
         
    path('', include(router.urls)),
]