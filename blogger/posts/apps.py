from django.apps import AppConfig


class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'

    def ready(self):
        import os
        # Avoid starting the thread twice when using the Django reloader
        if os.environ.get('RUN_MAIN', 'true') == 'true':
            from .utils import start_scheduled_post_publisher
            start_scheduled_post_publisher()
