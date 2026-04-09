from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from .serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """Javobida user rolini qo'shadigan maxsus token view"""
    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer
