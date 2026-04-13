from rest_framework import serializers
from .models import Post, Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "file", "description", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")


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
            "thumbnail",
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