from django.urls import path
from .views import CommentView, LikeView, ShareView

urlpatterns = [
    path("comments/", CommentView.as_view(), name="comment_list_create"),
    path("comments/<int:pk>/", CommentView.as_view(), name="comment_detail"),
    path("likes/", LikeView.as_view(), name="like_list_create"),
    path("shares/", ShareView.as_view(), name="share_list_create"),
]
