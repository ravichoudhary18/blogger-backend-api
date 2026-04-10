from django.contrib import admin
from .models import Comment, Like, Share


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("content", "user__username", "post__title")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "created_at")
    list_filter = ("created_at", "user")


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "platform", "created_at")
    list_filter = ("created_at", "user", "platform")
