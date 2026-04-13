import logging
import threading
import logging
from functools import wraps
from .models import Post, Document
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings

def run_in_background(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

def process_document_background(document_id):
    """
    Simulated background processing for a document.
    """
    try:
        document = Document.objects.get(id=document_id)
        logging.info(f"Starting background processing for Document {document_id}")
        # Simulated work
        logging.info(f"Finished background processing for Document {document_id}")

        # Send notification email
        send_mail(
            subject="File Upload Completed",
            message=f"Regarding your file upload: The document '{document.file.name}' has been successfully processed.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[document.post.author.email],
            fail_silently=True,
        )
    except Exception as e:
        logging.error(f"Error in background processing for Document {document_id}: {str(e)}")

def process_thumbnail_background(post_id, thumbnail_file_data, thumbnail_name):
    """
    Background job to save a thumbnail and update the post record.
    """
    try:
        post = Post.objects.get(id=post_id)
        logging.info(f"Saving thumbnail for Post {post_id} in background")
        
        # In a real app, you might want to resize the image here
        post.thumbnail.save(thumbnail_name, ContentFile(thumbnail_file_data))
        post.save()
        logging.info(f"Thumbnail saved for Post {post_id}")

        # Send notification email
        send_mail(
            subject="Thumbnail Processing Completed",
            message=f"Regarding your file upload: The thumbnail for your post '{post.title}' has been successfully processed.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[post.author.email],
            fail_silently=True,
        )
    except Exception as e:
        logging.error(f"Error saving thumbnail for Post {post_id}: {str(e)}")
