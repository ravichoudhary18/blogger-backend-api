from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    STATUS_CHOICES = (
        ("draft", "draft"),
        ("scheduled", "scheduled"),
        ("public", "public"),
        ("deleted", "deleted"),
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft",
    help_text="Select the publication status (draft, scheduled, public or deleted).")
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Publication date and time for scheduled posts.")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_posts"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="updated_posts"
    )
    total_likes = models.PositiveIntegerField(default=0, null=True, blank=True)
    total_comments = models.PositiveIntegerField(default=0, null=True, blank=True)
    total_shares = models.PositiveIntegerField(default=0, null=True, blank=True)
    thumbnail = models.ImageField(upload_to="thumbnails/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Document(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="documents/")
    description = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for {self.post.title}"
