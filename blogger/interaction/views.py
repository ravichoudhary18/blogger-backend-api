from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db import connection
from django.db.models import F
from .models import Comment, Like, Share
from posts.models import Post
from .serializers import CommentSerializer


class CommentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get(self, request, pk=None, *args, **kwargs):
        with connection.cursor() as cursor:
            if pk:
                # Still using ORM for single item as it's simple,
                # but could also be a function if needed.
                comment = get_object_or_404(Comment, pk=pk)
                serializer = CommentSerializer(comment)
                return Response(serializer.data)

            post_id = request.query_params.get("post")
            if not post_id:
                return Response(
                    {
                        "error": "Please provide a 'post' query parameter or a comment ID."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
                "SELECT get_comments_by_post(%s, %s, %s)", [post_id, limit, offset]
            )
            result = cursor.fetchone()[0]

            return Response(
                {
                    "count": result.get("count", 0),
                    "next": None
                    if offset + limit >= result.get("count", 0)
                    else f"?post={post_id}&page={page + 1}",
                    "previous": None
                    if page <= 1
                    else f"?post={post_id}&page={page - 1}",
                    "results": result.get("results", []),
                }
            )

    def post(self, request, *args, **kwargs):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(user=request.user)
            Post.objects.filter(pk=comment.post_id).update(total_comments=F("total_comments") + 1)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=pk)

        # Permission: comment author OR post author can delete
        is_comment_author = comment.user == request.user
        is_post_author = comment.post.author == request.user

        if not (is_comment_author or is_post_author):
            return Response(
                {"error": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        post_id = comment.post_id
        if comment.status != "deleted":
            comment.status = "deleted"
            comment.save()
            Post.objects.filter(pk=post_id).update(total_comments=F("total_comments") - 1)
        
        return Response(
            {"message": "Comment soft-deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class CommentHardDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, pk, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=pk)

        # Permission: comment author OR post author can delete
        is_comment_author = comment.user == request.user
        is_post_author = comment.post.author == request.user

        if not (is_comment_author or is_post_author):
            return Response(
                {"error": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        post_id = comment.post_id
        is_active = comment.status == "active"
        comment.delete()

        if is_active:
            Post.objects.filter(pk=post_id).update(total_comments=F("total_comments") - 1)

        return Response(
            {"message": "Comment permanently deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class LikeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post")
        if not post_id:
            return Response(
                {"error": "Please provide a 'post' query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT get_likes_by_post(%s, %s, %s)", [post_id, limit, offset]
            )
            result = cursor.fetchone()[0]

        return Response(
            {
                "count": result.get("count", 0),
                "next": None
                if offset + limit >= result.get("count", 0)
                else f"?post={post_id}&page={page + 1}",
                "previous": None if page <= 1 else f"?post={post_id}&page={page - 1}",
                "results": result.get("results", []),
            }
        )

    def post(self, request, *args, **kwargs):
        post_id = request.data.get("post")
        if not post_id:
            return Response(
                {"error": "Please provide a 'post' ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post = get_object_or_404(Post, pk=post_id)

        # Toggle like: create if not exists, delete if exists
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            if like.status == "active":
                like.status = "deleted"
                like.save()
                Post.objects.filter(pk=post_id).update(total_likes=F("total_likes") - 1)
                return Response(
                    {"message": "Post unliked successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                like.status = "active"
                like.save()
                Post.objects.filter(pk=post_id).update(total_likes=F("total_likes") + 1)
                return Response(
                    {"message": "Post liked successfully."},
                    status=status.HTTP_201_CREATED,
                )

        Post.objects.filter(pk=post_id).update(total_likes=F("total_likes") + 1)
        return Response(
            {"message": "Post liked successfully."},
            status=status.HTTP_201_CREATED,
        )


class LikeHardDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, pk, *args, **kwargs):
        like = get_object_or_404(Like, pk=pk)

        if like.user != request.user:
            return Response(
                {"error": "You do not have permission to delete this like."},
                status=status.HTTP_403_FORBIDDEN,
            )

        post_id = like.post_id
        is_active = like.status == "active"
        like.delete()

        if is_active:
            Post.objects.filter(pk=post_id).update(total_likes=F("total_likes") - 1)

        return Response(
            {"message": "Like permanently deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class ShareView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get(self, request, *args, **kwargs):
        post_id = request.query_params.get("post")
        if not post_id:
            return Response(
                {"error": "Please provide a 'post' query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT get_shares_by_post(%s, %s, %s)", [post_id, limit, offset]
            )
            result = cursor.fetchone()[0]

        return Response(
            {
                "count": result.get("count", 0),
                "next": None
                if offset + limit >= result.get("count", 0)
                else f"?post={post_id}&page={page + 1}",
                "previous": None if page <= 1 else f"?post={post_id}&page={page - 1}",
                "results": result.get("results", []),
            }
        )

    def post(self, request, *args, **kwargs):
        post_id = request.data.get("post")
        if not post_id:
            return Response(
                {"error": "Please provide a 'post' ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post = get_object_or_404(Post, pk=post_id)

        # Use get_or_create to avoid duplicate share records for the same user and post
        share, created = Share.objects.get_or_create(user=request.user, post=post)

        if created:
            Post.objects.filter(pk=post_id).update(total_shares=F("total_shares") + 1)

        # Generate shareable URL for the post
        base_url = request.build_absolute_uri("/")
        share_url = f"{base_url}api/posts/{post.id}/"

        return Response(
            {"url": share_url},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
