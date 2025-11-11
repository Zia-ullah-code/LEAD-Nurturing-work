from django.core.mail import EmailMessage
from django.conf import settings

def send_followup_email(lead, message, subject=None):
    """
    Sends a follow-up email to the lead with proper reply threading.
    """
    if not lead.email:
        print(f"No email for lead {lead.lead_name}")
        return False
    
    try:
        # Use custom subject if provided, otherwise default
        if not subject:
            subject = f"Follow-up about {lead.project_name}"
        
        # Create EmailMessage for better control over headers
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.EMAIL_HOST_USER,
            to=[lead.email],
        )
        
        # Get the most recent reply from the lead to thread the response
        from agent_app.models import LeadReply
        last_reply = lead.replies.order_by('-received_at').first()
        
        # Add threading headers for proper reply conversation threading
        if last_reply:
            message_id = f"<reply-{lead.id}-{last_reply.id}@{settings.EMAIL_HOST.replace('.', '_')}>"
            email.extra_headers = {
                'In-Reply-To': f"<msg-{lead.id}@{settings.EMAIL_HOST.replace('.', '_')}>",
                'References': f"<msg-{lead.id}@{settings.EMAIL_HOST.replace('.', '_')}>",
                'Message-ID': message_id,
            }
            print(f"[THREADING] Adding reply headers to thread with previous message")
        
        email.send(fail_silently=False)
        print(f"✅ Email sent to {lead.email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {lead.email}: {e}")
        return False
