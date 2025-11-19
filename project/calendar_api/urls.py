from django.urls import path
from . import views

urlpatterns = [
    path('create_event/', views.create_event, name='create_event'),
    path('schedule_weekly/', views.schedule_weekly, name='schedule_weekly'),
    path('update/<str:event_id>/', views.update_event, name='update_event'),
    path('delete/<str:event_id>/', views.delete_event, name='delete_event'),
]
