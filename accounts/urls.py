from django.urls import path
from .views import CustomTokenObtainPairView

app_name = 'accounts'

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]
