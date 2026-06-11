from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import CustomTokenObtainPairSerializer, ChangePasswordSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """Javobida user rolini qo'shadigan maxsus token view"""
    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


class ChangePasswordView(APIView):
    """Parolni o'zgartirish uchun API view"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Foydalanuvchi parolini o'zgartirish",
        operation_summary="Parolni o'zgartirish",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Parol muvaffaqiyatli o'zgartirildi",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Parol muvaffaqiyatli o'zgartirildi.",
                        "detail": "Yangi parolingiz bilan tizimga kirishingiz mumkin."
                    }
                }
            ),
            400: openapi.Response(
                description="Validatsiya xatoligi",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Parolni o'zgartirishda xatolik yuz berdi.",
                        "errors": {
                            "old_password": ["Joriy parol noto'g'ri kiritilgan."],
                            "new_password": ["Bu parol juda oddiy."],
                            "confirm_password": ["Yangi parol va tasdiqlash paroli bir xil bo'lishi kerak."]
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="Autentifikatsiya talab qilinadi",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            )
        },
        tags=['Accounts']
    )
    def post(self, request):
        """
        Foydalanuvchi parolini o'zgartirish
        
        Request body:
        {
            "old_password": "joriy_parol",
            "new_password": "yangi_parol", 
            "confirm_password": "yangi_parol_takrori"
        }
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Parol muvaffaqiyatli o\'zgartirildi.',
                'detail': 'Yangi parolingiz bilan tizimga kirishingiz mumkin.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Parolni o\'zgartirishda xatolik yuz berdi.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
