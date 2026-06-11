from django.urls import path
from .views import CircleListView, CircleDetailView

app_name = 'activities'

urlpatterns = [
    path('circles/', CircleListView.as_view(), name='circle-list'),
    path('circles/<slug:slug>/', CircleDetailView.as_view(), name='circle-detail'),
]
