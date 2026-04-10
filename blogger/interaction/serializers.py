from rest_framework import serializers
from .models import Comment, Like, Share


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

    class Meta:
        model = Share
        fields = (
            "id",
            "post",
            "user",
            "username",
            "platform",
            "created_at",
        )
        read_only_fields = ("user", "created_at")
