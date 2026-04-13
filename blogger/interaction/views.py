from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db import connection
from django.db.models import F
from .models import Comment, Like, Share
from posts.models import Post
import threading
from django.core.mail import send_mail
from django.contrib.auth.models import User
import difflib
from .serializers import (
    CommentSerializer,
    UserInteractionQuerySerializer,
    InteractionPostSerializer,
    ShareSerializer,
)


def send_share_emails(sender_username, post_title, share_url, recipient_emails):
    """
    Helper function to send emails in a background thread.
    """
    subject = f"{sender_username} shared a post with you!"
    message = f"Hello,\n\n{sender_username} thought you might like this post: {post_title}.\n\nYou can view it here: {share_url}\n\nHappy reading!"
    from_email = "noreply@blogger.com"
    
    try:
        send_mail(subject, message, from_email, recipient_emails)
    except Exception as e:
        # In a real app, you'd log this more robustly
        print(f"Error sending share emails: {str(e)}")


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

        if not is_comment_author:
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
        shared_with_ids = request.data.get("shared_with", [])

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

        # Handle recipients
        recipient_emails = []
        if shared_with_ids:
            recipients = User.objects.filter(id__in=shared_with_ids)
            share.shared_with.add(*recipients)
            recipient_emails = list(recipients.values_list("email", flat=True))
            # Remove empty/null emails
            recipient_emails = [email for email in recipient_emails if email]

        # Generate shareable URL for the post
        base_url = request.build_absolute_uri("/")
        share_url = f"{base_url}api/posts/{post.id}/"

        # If there are recipients, trigger the background thread
        if recipient_emails:
            email_thread = threading.Thread(
                target=send_share_emails,
                args=(request.user.username, post.title, share_url, recipient_emails),
            )
            email_thread.start()

        serializer = ShareSerializer(share)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class UserInteractionListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination

    def get(self, request, interaction_type, *args, **kwargs):
        # Retrieve username from authenticated request
        username = request.user.username

        # Validate using serializer
        query_data = {"username": username, "interaction_type": interaction_type}
        query_serializer = UserInteractionQuerySerializer(data=query_data)

        if not query_serializer.is_valid():
            # Provide hint if interaction_type is invalid
            valid_types = ["liked-posts", "commented-posts", "shared-posts"]
            error_msg = "Invalid interaction type."
            hint = ""
            
            close_matches = difflib.get_close_matches(interaction_type, valid_types, n=1, cutoff=0.6)
            if close_matches:
                hint = f" Did you mean '{close_matches[0]}'?"
            
            return Response(
                {
                    "error": f"{error_msg}{hint}",
                    "valid_options": valid_types,
                    "details": query_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = query_serializer.validated_data
        interaction_type = validated_data["interaction_type"]
        username = validated_data["username"]

        # Map interaction type to function name
        type_to_function = {
            "liked-posts": "get_liked_posts_by_user",
            "commented-posts": "get_commented_posts_by_user",
            "shared-posts": "get_shared_posts_by_user",
        }
        function_name = type_to_function[interaction_type]

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
                f"SELECT {function_name}(%s, %s, %s)",
                [username, limit, offset],
            )
            result = cursor.fetchone()[0]

        # Use serializer for output results
        results_serializer = InteractionPostSerializer(result.get("results", []), many=True)

        return Response(
            {
                "count": result.get("count", 0),
                "next": None
                if offset + limit >= result.get("count", 0)
                else f"?page={page + 1}",
                "previous": None if page <= 1 else f"?page={page - 1}",
                "interaction_type": interaction_type,
                "username": username,
                "results": results_serializer.data,
            }
        )
