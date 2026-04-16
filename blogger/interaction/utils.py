from django.core.mail import send_mail
from django.conf import settings

def send_share_emails(sender_username, post_title, share_url, recipient_emails):
    """
    Helper function to send emails one by one in a background thread.
    """
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@blogger.com")
    subject = f"{sender_username} shared a post with you!"
    
    for email in recipient_emails:
        message = f"Hello,\n\n{sender_username} thought you might like this post: {post_title}.\n\nYou can view it here: {share_url}\n\nHappy reading!"
        try:
            send_mail(subject, message, from_email, [email])
        except Exception as e:
            # In a real app, you'd log this more robustly
            print(f"Error sending share email to {email}: {str(e)}")
