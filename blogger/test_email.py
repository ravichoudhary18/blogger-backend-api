import os
import django
import sys

# Setup Django environment
sys.path.append('/app/blogger')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogger.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    print(f"Testing email sending with backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    
    subject = "Test Email from Blogger API"
    message = "This is a test email to verify that SMTP configuration is working."
    recipient_list = ["ravi.c@osplabs.com"]
    
    try:
        sent = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        if sent:
            print("SUCCESS: Email sent successfully.")
        else:
            print("FAILED: Email not sent.")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_email()
