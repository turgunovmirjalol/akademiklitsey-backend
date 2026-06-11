from django.urls import path
from .views import CustomTokenObtainPairView, ChangePasswordView

app_name = 'accounts'

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
