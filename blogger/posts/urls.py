from django.urls import path
from .views import PostView, HardDeleteView, UserPostView, DocumentView

urlpatterns = [
    path("", PostView.as_view(), name="post_list"),
    path("my-posts/", UserPostView.as_view(), name="user_posts"),
    path("create/", PostView.as_view(), name="post_create"),
    path("<int:pk>/", PostView.as_view(), name="post_detail"),
    path("<int:pk>/hard-delete/", HardDeleteView.as_view(), name="post_hard_delete"),
    path("<int:post_id>/documents/", DocumentView.as_view(), name="document_add"),
    path("documents/<int:pk>/", DocumentView.as_view(), name="document_delete"),
]
