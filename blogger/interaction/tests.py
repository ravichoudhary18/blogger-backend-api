from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from posts.models import Post
from .models import Comment, Like, Share


class InteractionTestBase(TestCase):
    """Base class with shared setup for all interaction tests."""

    def setUp(self):
        self.client = APIClient()

        # Create two users
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

        # Create a post authored by user1
        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.user1,
            created_by=self.user1,
            status="public",
        )

        # Authenticate as user1 by default
        self.client.force_authenticate(user=self.user1)


# ──────────────────────────────────────────────
#  COMMENT TESTS
# ──────────────────────────────────────────────
class CommentListByPostTest(InteractionTestBase):
    """GET /api/interaction/comments/?post=<id>"""

    def test_get_comments_by_post(self):
        Comment.objects.create(post=self.post, user=self.user1, content="Comment 1")
        Comment.objects.create(post=self.post, user=self.user2, content="Comment 2")
        resp = self.client.get("/api/interaction/comments/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_get_comments_missing_post_param(self):
        resp = self.client.get("/api/interaction/comments/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_comments_invalid_post(self):
        resp = self.client.get("/api/interaction/comments/", {"post": 9999})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_comments_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/interaction/comments/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentDetailTest(InteractionTestBase):
    """GET /api/interaction/comments/<pk>/"""

    def test_get_comment_by_id(self):
        comment = Comment.objects.create(
            post=self.post, user=self.user1, content="Hello"
        )
        resp = self.client.get(f"/api/interaction/comments/{comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["content"], "Hello")

    def test_get_comment_not_found(self):
        resp = self.client.get("/api/interaction/comments/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class CommentCreateTest(InteractionTestBase):
    """POST /api/interaction/comments/"""

    def test_create_comment(self):
        data = {"post": self.post.id, "content": "Nice post!"}
        resp = self.client.post("/api/interaction/comments/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["content"], "Nice post!")
        self.assertEqual(resp.data["user"], self.user1.id)
        self.assertEqual(Comment.objects.count(), 1)

    def test_create_comment_missing_content(self):
        data = {"post": self.post.id}
        resp = self.client.post("/api/interaction/comments/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_comment_missing_post(self):
        data = {"content": "No post?"}
        resp = self.client.post("/api/interaction/comments/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class CommentDeleteTest(InteractionTestBase):
    """DELETE /api/interaction/comments/<pk>/"""

    def test_delete_own_comment(self):
        comment = Comment.objects.create(
            post=self.post, user=self.user1, content="My comment"
        )
        resp = self.client.delete(f"/api/interaction/comments/{comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_post_author_can_delete_others_comment(self):
        # user2 comments on user1's post; user1 (post author) can delete it
        comment = Comment.objects.create(
            post=self.post, user=self.user2, content="User2 comment"
        )
        resp = self.client.delete(f"/api/interaction/comments/{comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_user_cannot_delete_comment(self):
        comment = Comment.objects.create(
            post=self.post, user=self.user1, content="User1 comment"
        )
        self.client.force_authenticate(user=self.user2)
        resp = self.client.delete(f"/api/interaction/comments/{comment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_delete_comment_not_found(self):
        resp = self.client.delete("/api/interaction/comments/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────
#  LIKE TESTS
# ──────────────────────────────────────────────
class LikeListByPostTest(InteractionTestBase):
    """GET /api/interaction/likes/?post=<id>"""

    def test_get_likes_by_post(self):
        Like.objects.create(post=self.post, user=self.user1)
        Like.objects.create(post=self.post, user=self.user2)
        resp = self.client.get("/api/interaction/likes/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_get_likes_empty(self):
        resp = self.client.get("/api/interaction/likes/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_get_likes_missing_post_param(self):
        resp = self.client.get("/api/interaction/likes/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_likes_invalid_post(self):
        resp = self.client.get("/api/interaction/likes/", {"post": 9999})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_likes_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/interaction/likes/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class LikeToggleTest(InteractionTestBase):
    """POST /api/interaction/likes/"""

    def test_like_post(self):
        resp = self.client.post(
            "/api/interaction/likes/", {"post": self.post.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), 1)

    def test_unlike_post(self):
        Like.objects.create(post=self.post, user=self.user1)
        resp = self.client.post(
            "/api/interaction/likes/", {"post": self.post.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Like.objects.count(), 0)

    def test_like_toggle_twice_returns_to_liked(self):
        # like → unlike → like
        self.client.post(
            "/api/interaction/likes/", {"post": self.post.id}, format="json"
        )
        self.client.post(
            "/api/interaction/likes/", {"post": self.post.id}, format="json"
        )
        resp = self.client.post(
            "/api/interaction/likes/", {"post": self.post.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Like.objects.count(), 1)

    def test_like_missing_post(self):
        resp = self.client.post("/api/interaction/likes/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_like_invalid_post(self):
        resp = self.client.post(
            "/api/interaction/likes/", {"post": 9999}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────
#  SHARE TESTS
# ──────────────────────────────────────────────
class ShareListByPostTest(InteractionTestBase):
    """GET /api/interaction/shares/?post=<id>"""

    def test_get_shares_by_post(self):
        Share.objects.create(post=self.post, user=self.user1)
        Share.objects.create(post=self.post, user=self.user2)
        resp = self.client.get("/api/interaction/shares/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_get_shares_empty(self):
        resp = self.client.get("/api/interaction/shares/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_get_shares_missing_post_param(self):
        resp = self.client.get("/api/interaction/shares/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_shares_invalid_post(self):
        resp = self.client.get("/api/interaction/shares/", {"post": 9999})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_shares_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/interaction/shares/", {"post": self.post.id})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ShareCreateTest(InteractionTestBase):
    """POST /api/interaction/shares/"""

    def test_create_share_returns_url(self):
        resp = self.client.post(
            "/api/interaction/shares/", {"post": self.post.id}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("url", resp.data)
        self.assertIn(f"/api/posts/{self.post.id}/", resp.data["url"])
        self.assertEqual(Share.objects.count(), 1)

    def test_create_share_platform_is_null(self):
        self.client.post(
            "/api/interaction/shares/", {"post": self.post.id}, format="json"
        )
        share = Share.objects.first()
        self.assertIsNone(share.platform)

    def test_create_multiple_shares_allowed(self):
        self.client.post(
            "/api/interaction/shares/", {"post": self.post.id}, format="json"
        )
        self.client.post(
            "/api/interaction/shares/", {"post": self.post.id}, format="json"
        )
        self.assertEqual(Share.objects.count(), 2)

    def test_create_share_missing_post(self):
        resp = self.client.post("/api/interaction/shares/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_share_invalid_post(self):
        resp = self.client.post(
            "/api/interaction/shares/", {"post": 9999}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
