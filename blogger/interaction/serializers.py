from rest_framework import serializers
from .models import Comment, Like, Share
from posts.models import Post



class CommentSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "user",
            "username",
            "content",
            "created_at",
        )
        read_only_fields = ("user", "created_at")


class LikeSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Like
        fields = (
            "id",
            "post",
            "user",
            "username",
            "created_at",
        )
        read_only_fields = ("user", "created_at")


class ShareSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")
    shared_with_details = serializers.StringRelatedField(source="shared_with", many=True, read_only=True)

    class Meta:
        model = Share
        fields = (
            "id",
            "post",
            "user",
            "username",
            "platform",
            "shared_with",
            "shared_with_details",
            "created_at",
        )
        read_only_fields = ("user", "created_at")

class InteractionPostSerializer(serializers.ModelSerializer):
    author = serializers.IntegerField(read_only=True)
    author_username = serializers.CharField(read_only=True)
    shared_with = serializers.JSONField(read_only=True, required=False)
    last_commented_at = serializers.DateTimeField(read_only=True, required=False)

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "content",
            "thumbnail",
            "author",
            "author_username",
            "shared_with",
            "created_at",
            "updated_at",
            "last_commented_at",
        )


class UserInteractionQuerySerializer(serializers.Serializer):
    interaction_type = serializers.ChoiceField(
        choices=[
            ("liked-posts", "Liked Posts"),
            ("commented-posts", "Commented Posts"),
            ("shared-posts", "Shared Posts"),
        ]
    )
    username = serializers.CharField(max_length=150)
