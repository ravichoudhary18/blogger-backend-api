from datetime import datetime
from django.db import connection
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Post
from .serializers import PostSerializer


class PostView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get_token_iat(self):
        token_iat_timestamp = self.request.auth.get("iat")
        if token_iat_timestamp:
            return datetime.fromtimestamp(
                token_iat_timestamp, tz=timezone.get_current_timezone()
            )
        return timezone.now()

    def get(self, request, pk=None, *args, **kwargs):
        with connection.cursor() as cursor:
            if pk:
                cursor.execute("SELECT get_post_by_id(%s)", [pk])
                result = cursor.fetchone()[0]
                if not result:
                    return Response(
                        {"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND
                    )
                return Response(result)

            # Filtering logic from query params - convert empty strings to None
            title = request.query_params.get("title") or None
            author = request.query_params.get("author") or None
            start_date = request.query_params.get("start_date") or None
            end_date = request.query_params.get("end_date") or None

            # Pagination logic
            try:
                limit = int(request.query_params.get("page_size", 10))
            except (ValueError, TypeError):
                limit = 10

            try:
                page = int(request.query_params.get("page", 1))
            except (ValueError, TypeError):
                page = 1
            offset = (page - 1) * limit

            cursor.execute(
                "SELECT get_posts(%s, %s, %s, %s, %s, %s)",
                [title, author, start_date, end_date, limit, offset],
            )
            result = cursor.fetchone()[0]

            # Construct paginated response similar to DRF for consistency
            count = result.get("count", 0)
            posts = result.get("results", [])

            # Simple manual pagination links (or use DRF's helper if preferred)
            return Response(
                {
                    "count": count,
                    "next": None if offset + limit >= count else f"?page={page + 1}",
                    "previous": None if page <= 1 else f"?page={page - 1}",
                    "results": posts,
                }
            )

    def post(self, request, *args, **kwargs):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            system_now = timezone.now()
            token_iat = self.get_token_iat()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "CALL add_post(%s, %s, %s, %s, %s, %s)",
                        [
                            serializer.validated_data["title"],
                            serializer.validated_data["content"],
                            request.user.id,
                            serializer.validated_data.get("status", "draft"),
                            system_now,
                            token_iat,
                        ],
                    )
                return Response(
                    {"message": "Post created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"error": "Database error", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk, partial=False):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostSerializer(post, data=request.data, partial=partial)
        if serializer.is_valid():
            token_iat = self.get_token_iat()
            if partial and set(serializer.validated_data.keys()) == {"status"}:
                proc = "update_post_status(%s, %s, %s, %s)"
                params = [
                    pk,
                    serializer.validated_data["status"],
                    request.user.id,
                    token_iat,
                ]
            else:
                proc = "update_post(%s, %s, %s, %s, %s, %s)"
                params = [
                    pk,
                    serializer.validated_data.get("title", post.title),
                    serializer.validated_data.get("content", post.content),
                    serializer.validated_data.get("status", post.status),
                    request.user.id,
                    token_iat,
                ]

            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"CALL {proc}", params)
                return Response({"message": "Post updated successfully."})
            except Exception as e:
                return Response(
                    {"error": "Database error", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        return self.update(request, pk, partial=False)

    def patch(self, request, pk, *args, **kwargs):
        return self.update(request, pk, partial=True)

    def delete(self, request, pk, *args, **kwargs):
        get_object_or_404(Post, pk=pk)
        token_iat = self.get_token_iat()
        try:
            with connection.cursor() as cursor:
                # Switching to soft-delete using update_post_status SP
                cursor.execute(
                    "CALL update_post_status(%s, %s, %s, %s)",
                    [pk, "deleted", request.user.id, token_iat],
                )
            return Response(
                {"message": "Post marked as deleted."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "Database error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HardDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, pk, *args, **kwargs):
        get_object_or_404(Post, pk=pk)
        try:
            with connection.cursor() as cursor:
                cursor.execute("CALL delete_post(%s)", [pk])
            return Response(
                {"message": "Post permanently deleted (Hard Delete)."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "Database error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
