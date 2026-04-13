import os
import django
import sys
from datetime import timedelta
from django.utils import timezone
from django.db import connection

# Setup Django
sys.path.append('/app/blogger')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogger.settings')
django.setup()

from posts.models import Post
from django.contrib.auth.models import User

def verify_post_boost():
    try:
        user = User.objects.get(username='ravi')
        now = timezone.now()
        
        # 1. Post with 1 hour ago (within boost window)
        post_1 = Post.objects.create(
            title="Boosted Post",
            content="This post should have a boost.",
            author=user,
            status="public"
        )
        post_1.created_at = now - timedelta(hours=1)
        post_1.save()
        # Force update created_at via SQL because auto_now_add=True makes it hard to change via ORM save()
        with connection.cursor() as cursor:
            cursor.execute("UPDATE posts_post SET created_at = %s WHERE id = %s", [post_1.created_at, post_1.id])

        # 2. Post with 4 hours ago (outside boost window)
        post_2 = Post.objects.create(
            title="Expired Boost Post",
            content="This post boost should be gone.",
            author=user,
            status="public"
        )
        post_2.created_at = now - timedelta(hours=4)
        post_2.save()
        with connection.cursor() as cursor:
            cursor.execute("UPDATE posts_post SET created_at = %s WHERE id = %s", [post_2.created_at, post_2.id])

        # 3. Post before 2026-04-11
        post_3 = Post.objects.create(
            title="Old Post",
            content="This post was created before the boost feature started.",
            author=user,
            status="public"
        )
        post_3.created_at = timezone.make_aware(timezone.datetime(2026, 4, 10, 12, 0, 0))
        post_3.save()
        with connection.cursor() as cursor:
            cursor.execute("UPDATE posts_post SET created_at = %s WHERE id = %s", [post_3.created_at, post_3.id])

        # Verify via get_posts SQL
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_posts()")
            result = cursor.fetchone()[0]
            posts = result.get('results', [])
            
            for p in posts:
                if p['id'] == post_1.id:
                    print(f"Post 1 (1h ago): Boost = {p.get('post_boost')}")
                    if p.get('post_boost') and "boost remaining" in p.get('post_boost'):
                        print("SUCCESS: Post 1 has correct boost message.")
                    else:
                        print("FAILED: Post 1 missing boost message.")
                
                if p['id'] == post_2.id:
                    print(f"Post 2 (4h ago): Boost = {p.get('post_boost')}")
                    if p.get('post_boost') is None:
                        print("SUCCESS: Post 2 has no boost message (expired).")
                    else:
                        print("FAILED: Post 2 still has boost message.")

                if p['id'] == post_3.id:
                    print(f"Post 3 (Before 2026-04-11): Boost = {p.get('post_boost')}")
                    if p.get('post_boost') is None:
                        print("SUCCESS: Post 3 has no boost message (too old).")
                    else:
                        print("FAILED: Post 3 has boost message despite being old.")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    verify_post_boost()
