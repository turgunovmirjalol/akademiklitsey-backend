from django.urls import path
from .views import (
    ContactMessageCreateView,
    ContactMessageListView,
    ContactMessageDetailView,
    ContactMessageReplyView,
    ContactMessageStatusView,
    ContactMessageStatsView,
)

app_name = 'contact'

urlpatterns = [
    # Public — xabar yuborish
    path('send/', ContactMessageCreateView.as_view(), name='contact-send'),
    
    # Admin — ro'yxat va statistika
    path('messages/', ContactMessageListView.as_view(), name='contact-list'),
    path('messages/stats/', ContactMessageStatsView.as_view(), name='contact-stats'),
    
    # Admin — bitta xabar
    path('messages/<int:pk>/', ContactMessageDetailView.as_view(), name='contact-detail'),
    path('messages/<int:pk>/reply/', ContactMessageReplyView.as_view(), name='contact-reply'),
    path('messages/<int:pk>/status/', ContactMessageStatusView.as_view(), name='contact-status'),
]
