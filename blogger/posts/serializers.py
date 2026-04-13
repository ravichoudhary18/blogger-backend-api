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
            "invalid_choice": "Invalid status. Allowed values are: draft, scheduled, public or deleted."
        }
    )
    post_boost = serializers.CharField(read_only=True, required=False)

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
            "scheduled_at",
            "post_boost",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "author": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "status": {"required": False},
        }

    def validate(self, data):
        """
        Custom validation to ensure scheduled_at is provided if status is 'scheduled'.
        """
        status = data.get("status")
        scheduled_at = data.get("scheduled_at")

        # In case of partial update (PATCH), we might need to check the instance
        if not status and self.instance:
            status = self.instance.status
        if not scheduled_at and self.instance:
            scheduled_at = self.instance.scheduled_at

        if status == "scheduled" and not scheduled_at:
            raise serializers.ValidationError(
                {"scheduled_at": "This field is required when status is 'scheduled'."}
            )
        
        return data