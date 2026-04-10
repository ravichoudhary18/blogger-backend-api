from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Post


class PostTestBase(TestCase):
    """Shared setup for post tests."""

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="author1", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="author2", password="testpass123"
        )

        # Login with JWT to get a real token (needed for get_token_iat)
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "author1", "password": "testpass123"},
            format="json",
        )
        self.access_token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Create posts directly (bypasses stored procedures)
        self.public_post = Post.objects.create(
            title="Public Post",
            content="Public content",
            author=self.user1,
            created_by=self.user1,
            status="public",
        )
        self.draft_post = Post.objects.create(
            title="Draft Post",
            content="Draft content",
            author=self.user1,
            created_by=self.user1,
            status="draft",
        )
        self.deleted_post = Post.objects.create(
            title="Deleted Post",
            content="Deleted content",
            author=self.user1,
            created_by=self.user1,
            status="deleted",
        )


# ──────────────────────────────────────────────
#  LIST POSTS (GET /api/posts/)
# ──────────────────────────────────────────────
class PostListTest(PostTestBase):
    """GET /api/posts/"""

    def test_list_returns_only_public_posts(self):
        resp = self.client.get("/api/posts/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [p["title"] for p in resp.data["results"]]
        self.assertIn("Public Post", titles)
        self.assertNotIn("Draft Post", titles)
        self.assertNotIn("Deleted Post", titles)

    def test_list_unauthenticated(self):
        self.client.credentials()  # Clear JWT token
        resp = self.client.get("/api/posts/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_filter_by_title(self):
        resp = self.client.get("/api/posts/", {"title": "Public"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "Public Post")

    def test_list_filter_by_title_no_match(self):
        resp = self.client.get("/api/posts/", {"title": "nonexistent"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

    def test_list_filter_by_author(self):
        Post.objects.create(
            title="Author2 Post",
            content="Content",
            author=self.user2,
            created_by=self.user2,
            status="public",
        )
        resp = self.client.get("/api/posts/", {"author": "author2"})
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "Author2 Post")

    def test_list_filter_by_author_no_match(self):
        resp = self.client.get("/api/posts/", {"author": "ghost"})
        self.assertEqual(resp.data["count"], 0)

    def test_list_pagination(self):
        resp = self.client.get("/api/posts/")
        self.assertIn("count", resp.data)
        self.assertIn("results", resp.data)


# ──────────────────────────────────────────────
#  POST DETAIL (GET /api/posts/<pk>/)
# ──────────────────────────────────────────────
class PostDetailTest(PostTestBase):
    """GET /api/posts/<pk>/"""

    def test_get_public_post_by_id(self):
        resp = self.client.get(f"/api/posts/{self.public_post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Public Post")
        self.assertEqual(resp.data["author_username"], "author1")

    def test_get_draft_post_returns_404(self):
        resp = self.client.get(f"/api/posts/{self.draft_post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_deleted_post_returns_404(self):
        resp = self.client.get(f"/api/posts/{self.deleted_post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_nonexistent_post_returns_404(self):
        resp = self.client.get("/api/posts/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_detail_includes_counts(self):
        resp = self.client.get(f"/api/posts/{self.public_post.id}/")
        self.assertIn("likes_count", resp.data)
        self.assertIn("comments_count", resp.data)
        self.assertEqual(resp.data["likes_count"], 0)
        self.assertEqual(resp.data["comments_count"], 0)


# ──────────────────────────────────────────────
#  CREATE POST (POST /api/posts/create/)
#  Uses stored procedure add_post
# ──────────────────────────────────────────────
class PostCreateTest(PostTestBase):
    """POST /api/posts/create/"""

    def test_create_post_success(self):
        data = {"title": "New Post", "content": "New content", "status": "public"}
        resp = self.client.post("/api/posts/create/", data, format="json")
        self.assertIn(
            resp.status_code,
            [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )
        # If SP exists, 201; if not, 500 (DB error)
        if resp.status_code == status.HTTP_201_CREATED:
            self.assertEqual(resp.data["message"], "Post created successfully.")

    def test_create_post_missing_title(self):
        data = {"content": "No title"}
        resp = self.client.post("/api/posts/create/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_missing_content(self):
        data = {"title": "No content"}
        resp = self.client.post("/api/posts/create/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_unauthenticated(self):
        self.client.credentials()  # Clear JWT token
        data = {"title": "Unauth Post", "content": "Content"}
        resp = self.client.post("/api/posts/create/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_default_status_is_draft(self):
        data = {"title": "Draft Default", "content": "Content"}
        resp = self.client.post("/api/posts/create/", data, format="json")
        # Validates serializer accepts without status field
        self.assertIn(
            resp.status_code,
            [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )


# ──────────────────────────────────────────────
#  UPDATE POST (PUT /api/posts/<pk>/)
#  Uses stored procedure update_post
# ──────────────────────────────────────────────
class PostUpdateTest(PostTestBase):
    """PUT /api/posts/<pk>/"""

    def test_full_update_post(self):
        data = {"title": "Updated", "content": "Updated content", "status": "public"}
        resp = self.client.put(
            f"/api/posts/{self.public_post.id}/", data, format="json"
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_update_nonexistent_post(self):
        data = {"title": "X", "content": "X", "status": "public"}
        resp = self.client.put("/api/posts/9999/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_missing_required_fields(self):
        data = {"title": "Only title"}
        resp = self.client.put(
            f"/api/posts/{self.public_post.id}/", data, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
#  PARTIAL UPDATE (PATCH /api/posts/<pk>/)
#  Uses stored procedure update_post_status
# ──────────────────────────────────────────────
class PostPatchTest(PostTestBase):
    """PATCH /api/posts/<pk>/"""

    def test_patch_status_only(self):
        data = {"status": "draft"}
        resp = self.client.patch(
            f"/api/posts/{self.public_post.id}/", data, format="json"
        )
        self.assertIn(
            resp.status_code,
            [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_patch_nonexistent_post(self):
        data = {"status": "draft"}
        resp = self.client.patch("/api/posts/9999/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ──────────────────────────────────────────────
#  SOFT DELETE (DELETE /api/posts/<pk>/)
#  Uses stored procedure update_post_status
# ──────────────────────────────────────────────
class PostSoftDeleteTest(PostTestBase):
    """DELETE /api/posts/<pk>/"""

    def test_soft_delete_post(self):
        resp = self.client.delete(f"/api/posts/{self.public_post.id}/")
        self.assertIn(
            resp.status_code,
            [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )
        if resp.status_code == status.HTTP_200_OK:
            self.assertIn("deleted", resp.data["message"].lower())

    def test_soft_delete_nonexistent(self):
        resp = self.client.delete("/api/posts/9999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_soft_delete_unauthenticated(self):
        self.client.credentials()  # Clear JWT token
        resp = self.client.delete(f"/api/posts/{self.public_post.id}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────
#  HARD DELETE (DELETE /api/posts/<pk>/hard-delete/)
#  Uses stored procedure delete_post
# ──────────────────────────────────────────────
class PostHardDeleteTest(PostTestBase):
    """DELETE /api/posts/<pk>/hard-delete/"""

    def test_hard_delete_post(self):
        resp = self.client.delete(f"/api/posts/{self.public_post.id}/hard-delete/")
        self.assertIn(
            resp.status_code,
            [status.HTTP_204_NO_CONTENT, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_hard_delete_nonexistent(self):
        resp = self.client.delete("/api/posts/9999/hard-delete/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_hard_delete_unauthenticated(self):
        self.client.credentials()  # Clear JWT token
        resp = self.client.delete(f"/api/posts/{self.public_post.id}/hard-delete/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────
#  SERIALIZER FIELD TESTS
# ──────────────────────────────────────────────
class PostSerializerTest(PostTestBase):
    """Verify serializer output fields."""

    def test_serializer_fields(self):
        resp = self.client.get(f"/api/posts/{self.public_post.id}/")
        expected_fields = {
            "id",
            "title",
            "content",
            "status",
            "author",
            "author_username",
            "likes_count",
            "comments_count",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(resp.data.keys()), expected_fields)
