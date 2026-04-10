import logging
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, MyTokenObtainPairSerializer


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as e:
            logging.error(
                f"Login failed for user: {request.data.get('username') or request.data.get('email')} - Error: {str(e)}"
            )
            return Response(
                {"detail": "Invalid credentials or login error."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        logging.info(
            f"Registration attempt for username: {request.data.get('username')}"
        )
        try:
            response = super().post(request, *args, **kwargs)
            logging.info(
                f"User {request.data.get('username')} registered successfully."
            )
            return response
        except Exception as e:
            logging.error(
                f"Registration failed for username: {request.data.get('username')} - Error: {str(e)}"
            )
            return Response(
                {"error": "Registration failed.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
