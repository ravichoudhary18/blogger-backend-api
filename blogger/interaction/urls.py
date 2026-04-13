from django.urls import path
from .views import CommentView, CommentHardDeleteView, LikeView, LikeHardDeleteView, ShareView, UserInteractionListView

urlpatterns = [
    path("comments/", CommentView.as_view(), name="comment_list_create"),
    path("comments/<int:pk>/", CommentView.as_view(), name="comment_detail"),
    path("comments/<int:pk>/hard-delete/", CommentHardDeleteView.as_view(), name="comment_hard_delete"),
    path("likes/", LikeView.as_view(), name="like_list_create"),
    path("likes/<int:pk>/hard-delete/", LikeHardDeleteView.as_view(), name="like_hard_delete"),
    path("shares/", ShareView.as_view(), name="share_list_create"),
    path(
        "my/<str:interaction_type>/",
        UserInteractionListView.as_view(),
        name="user_interaction_history",
    ),
]
