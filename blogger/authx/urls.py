from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .views import RegisterView, MyTokenObtainPairView

urlpatterns = [
    path("login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("register/", RegisterView.as_view(), name="auth_register"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
