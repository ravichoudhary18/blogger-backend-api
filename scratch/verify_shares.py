from django.db import connection, transaction
from django.contrib.auth.models import User
from posts.models import Post
from interaction.models import Share
import json
import sys

def verify_shared_with():
    try:
        # 1. Setup data
        user_ravi = User.objects.get(username='ravi')
        user_demo = User.objects.get(username='demo_user')
        post = Post.objects.first()
        
        if not post:
            print("SQL_VERIFICATION: FAILED: No posts found.")
            return

        with transaction.atomic():
            # Create a share record if it doesn't exist
            share, created = Share.objects.get_or_create(user=user_ravi, post=post)
            # Add demo_user as recipient
            share.shared_with.add(user_demo)
            print(f"SQL_VERIFICATION: Shared post {post.id} with user {user_demo.id}")

        # 2. Test get_shared_posts_by_user
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_shared_posts_by_user(%s)", ['ravi'])
            row = cursor.fetchone()
            data = row[0]
            print("SQL_VERIFICATION: get_shared_posts_by_user worked.")
            
            # Check if shared_with is in the results
            results = data.get('results', [])
            if results:
                for res in results:
                    if res.get('id') == post.id:
                        print(f"SQL_VERIFICATION: Found shared_with in result: {res.get('shared_with')}")
                        if user_demo.id in res.get('shared_with'):
                            print("SQL_VERIFICATION: SUCCESS: Recipient ID found in shared_with list.")
                        else:
                            print("SQL_VERIFICATION: FAILED: Recipient ID NOT found in shared_with list.")
            else:
                print("SQL_VERIFICATION: FAILED: No results returned from get_shared_posts_by_user.")

    except Exception as e:
        print(f"SQL_VERIFICATION: FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_shared_with()
