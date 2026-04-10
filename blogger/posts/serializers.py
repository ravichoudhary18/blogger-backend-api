from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source="author.username")
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()
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
            "likes_count",
            "comments_count",
            "share_count",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "author": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "status": {"required": False},
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_share_count(self, obj):
        return obj.shares.count()
