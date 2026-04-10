from django.urls import path
from .views import PostView, HardDeleteView

urlpatterns = [
    path("", PostView.as_view(), name="post_list"),
    path("create/", PostView.as_view(), name="post_create"),
    path("<int:pk>/", PostView.as_view(), name="post_detail"),
    path("<int:pk>/hard-delete/", HardDeleteView.as_view(), name="post_hard_delete"),
]
