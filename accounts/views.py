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
    """API view for changing user password"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change user password",
        operation_summary="Change password",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Password changed successfully.",
                        "detail": "You can now log in with your new password."
                    }
                }
            ),
            400: openapi.Response(
                description="Validation error",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Password change failed.",
                        "errors": {
                            "old_password": ["Current password is incorrect."],
                            "new_password": ["This password is too common."],
                            "confirm_password": ["New password and confirmation do not match."]
                        }
                    }
                }
            ),
            401: openapi.Response(
                description="Authentication required",
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
        Change user password

        Request body:
        {
            "old_password": "current_password",
            "new_password": "new_password",
            "confirm_password": "confirm_new_password"
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
                'message': 'Password changed successfully.',
                'detail': 'You can now log in with your new password.'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Password change failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
