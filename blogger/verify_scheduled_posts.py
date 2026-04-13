import os
import django
import sys
import time
from datetime import timedelta
from django.utils import timezone
from django.db import connection

# Setup Django
sys.path.append('/app/blogger')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogger.settings')
django.setup()

from posts.models import Post
from django.contrib.auth.models import User

def verify_scheduled_posts():
    try:
        user = User.objects.get(username='ravi')
        
        # 1. Create a post scheduled for 5 seconds from now
        now = timezone.now()
        scheduled_time = now + timedelta(seconds=5)
        
        print(f"Creating scheduled post at {scheduled_time}")
        post = Post.objects.create(
            title="Scheduled Post Test",
            content="This should become public soon.",
            author=user,
            status="scheduled",
            scheduled_at=scheduled_time
        )
        
        # 2. Check public feed (SQL function)
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_posts()")
            result = cursor.fetchone()[0]
            posts = result.get('results', [])
            titles = [p['title'] for p in posts]
            
            if post.title in titles:
                print("FAILED: Scheduled post visible in public feed before its time.")
            else:
                print("SUCCESS: Scheduled post NOT visible in public feed yet.")

        # 3. Wait 10 seconds (so it is due according to SQL logic)
        print("Waiting 10 seconds...")
        time.sleep(10)
        
        # 4. Check public feed again (SQL logic should allow it now even if status is still 'scheduled')
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_posts()")
            result = cursor.fetchone()[0]
            posts = result.get('results', [])
            titles = [p['title'] for p in posts]
            
            if post.title in titles:
                print("SUCCESS: Scheduled post IS visible in public feed after its time (via SQL logic).")
            else:
                print("FAILED: Scheduled post NOT visible in public feed even after its time.")

        # 5. Check if background worker updates status to 'public'
        # Note: Worker runs every 60s. We'll wait a bit longer.
        print("Waiting for background worker to update status to 'public' (up to 70s)...")
        time.sleep(70)
        
        post.refresh_from_db()
        print(f"Post status is now: {post.status}")
        if post.status == 'public':
            print("SUCCESS: Background worker updated status to 'public'.")
        else:
            print("FAILED: Background worker did NOT update status to 'public'.")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    verify_scheduled_posts()
