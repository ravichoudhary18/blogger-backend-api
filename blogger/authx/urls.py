from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .views import RegisterView, MyTokenObtainPairView, UserListView

urlpatterns = [
    path("login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("register/", RegisterView.as_view(), name="auth_register"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
