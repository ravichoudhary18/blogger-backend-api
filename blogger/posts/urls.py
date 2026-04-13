from django.urls import path
from .views import PostView, HardDeleteView, UserPostView

urlpatterns = [
    path("", PostView.as_view(), name="post_list"),
    path("my-posts/", UserPostView.as_view(), name="user_posts"),
    path("create/", PostView.as_view(), name="post_create"),
    path("<int:pk>/", PostView.as_view(), name="post_detail"),
    path("<int:pk>/hard-delete/", HardDeleteView.as_view(), name="post_hard_delete"),
]
