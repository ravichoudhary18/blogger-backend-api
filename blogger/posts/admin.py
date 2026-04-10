from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("status", "author", "created_at")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if not getattr(obj, "author", None):
                obj.author = request.user
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
