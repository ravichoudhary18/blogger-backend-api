from datetime import datetime
from django.db import connection
from django.utils import timezone
from rest_framework import status, permissions, parsers
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from .models import Post, Document
from .serializers import PostSerializer, DocumentSerializer
from .utils import process_document_background, process_thumbnail_background, run_in_background
import os
import logging


class PostView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
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
            
            thumbnail = request.FILES.get("thumbnail")
            thumbnail_bytes = None
            thumbnail_name = None
            if thumbnail:
                thumbnail_bytes = thumbnail.read()
                thumbnail_name = thumbnail.name

            try:
                with connection.cursor() as cursor:
                    # Using SELECT instead of CALL as we changed the procedure to a function
                    cursor.execute(
                        "SELECT add_post(%s, %s, %s, %s, %s, %s, %s, %s)",
                        [
                            serializer.validated_data["title"],
                            serializer.validated_data["content"],
                            request.user.id,
                            serializer.validated_data.get("status", "draft"),
                            system_now,
                            token_iat,
                            None, # Backgrounding thumbnail
                            serializer.validated_data.get("scheduled_at"),
                        ],
                    )
                    post_id = cursor.fetchone()[0]

                if thumbnail_bytes:
                    run_in_background(process_thumbnail_background)(post_id, thumbnail_bytes, thumbnail_name)

                return Response(
                    {"message": "Post created successfully.", "id": post_id},
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
        if post.author != request.user:
            return Response(
                {"error": "You do not have permission to update this post."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = PostSerializer(post, data=request.data, partial=partial)
        if serializer.is_valid():
            token_iat = self.get_token_iat()
            thumbnail_bytes = None
            thumbnail_name = None

            if partial and set(serializer.validated_data.keys()) == {"status"}:
                proc = "update_post_status(%s, %s, %s, %s)"
                params = [
                    pk,
                    serializer.validated_data["status"],
                    request.user.id,
                    token_iat,
                ]
            else:
                thumbnail = request.FILES.get("thumbnail")
                if thumbnail:
                    thumbnail_bytes = thumbnail.read()
                    thumbnail_name = thumbnail.name

                proc = "update_post(%s, %s, %s, %s, %s, %s, %s, %s)"
                params = [
                    pk,
                    serializer.validated_data.get("title", post.title),
                    serializer.validated_data.get("content", post.content),
                    serializer.validated_data.get("status", post.status),
                    request.user.id,
                    token_iat,
                    None, # Backgrounding thumbnail update
                    serializer.validated_data.get("scheduled_at", post.scheduled_at),
                ]

            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"CALL {proc}", params)
                
                if thumbnail_bytes:
                    run_in_background(process_thumbnail_background)(pk, thumbnail_bytes, thumbnail_name)
                    
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
        post = get_object_or_404(Post, pk=pk)
        if post.author != request.user:
            return Response(
                {"error": "You do not have permission to delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )
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
        post = get_object_or_404(Post, pk=pk)
        if post.author != request.user:
            return Response(
                {"error": "You do not have permission to permanently delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )
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


class UserPostView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        # Retrieve all non-deleted posts for the logged-in user including drafts
        queryset = Post.objects.filter(author=request.user).exclude(status='deleted').order_by('-created_at')

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        if paginated_queryset is not None:
            serializer = PostSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = PostSerializer(queryset, many=True)
        return Response(serializer.data)


class DocumentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        # Check if the user is the author
        if post.author != request.user:
            return Response(
                {"error": "You are not authorized to add documents to this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        description = request.data.get("description", "")
        
        document = Document.objects.create(
            post=post,
            file=file,
            description=description
        )

        # Trigger background processing
        run_in_background(process_document_background)(document.id)
        
        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        if document.post.author != request.user:
            return Response(
                {"error": "You are not authorized to delete this document."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        file_path = document.file.path
        document.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return Response({"message": "Document deleted successfully."}, status=status.HTTP_200_OK)
