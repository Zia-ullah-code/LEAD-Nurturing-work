from django.core.mail import send_mail
from django.conf import settings
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_backend.settings")
django.setup()

send_mail(
    "Test Email from Django",
    "Hi! This is a test message from your backend.",
    settings.EMAIL_HOST_USER,
    ["laybafiaz.trainee@devsinc.com"],  # receiver email
    fail_silently=False,
)

print("✅ Email sent successfully!")
