from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source="author.username")
    status = serializers.ChoiceField(
        choices=Post.STATUS_CHOICES,
        required=False,
        error_messages={
            "invalid_choice": "Invalid status. Allowed values are: draft, public or deleted."
        }
    )

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "content",
            "status",
            "author",
            "author_username",
            "total_likes",
            "total_comments",
            "total_shares",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "author": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "status": {"required": False},
        }