# agent_app/ai_message_service.py

import google.generativeai as genai, os,sys
from agent_app.models import Lead, Campaign, LeadReply
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ragImplementation")))

from rag_main import query
from agent_app.models import FollowUpMessage

from django.core.mail import send_mail, EmailMessage
from django.conf import settings

# Configure Gemini
genai.configure(api_key="AIzaSyDqfiqXi1CFvWM_YlW64BCKYJnOlmfZn_o")






def generate_message(lead, campaign):
    """
    Generate personalized AI message using Gemini + RAG context.
    Falls back gracefully if RAG fails.
    """
    try:
        # 1️⃣ Prepare prompt
        prompt = f"""
                You are an AI property sales assistant for a luxury real estate company.

                LEAD CONTEXT:
                - Name: {lead.lead_name}
                - Previously interested in: {lead.project_name}
                - Last conversation: {lead.last_conversation_summary or 'No prior context'}
                - Preferences: {lead.unit_type} unit, Budget: AED {lead.min_budget:,} - AED {lead.max_budget:,}

                TASK:
                Write a personalized follow-up email that:
                1. Acknowledges their previous interest in {lead.project_name}
                2. References their last conversation if available
                3. Positions {campaign.project_name} as a better match for their preferences
                4. Highlights the special offer: "{campaign.sales_offer}"
                5. Ends with a clear call-to-action

                REQUIREMENTS:
                - Professional but friendly tone
                - Concise (max 200 words)
                - Use the lead's actual name and specific preferences
                - Do NOT include placeholder text or generic language
                - Make it feel personal, not templated
                """

        # 2️⃣ Use RAG for richer context (graceful degradation)
        try:
            project_info = query(f"Compare {lead.project_name} and {campaign.project_name}")
            context = " ".join([r.page_content for r in project_info]) if project_info else ""
            print(f"[RAG] Retrieved {len(project_info) if project_info else 0} context documents")
        except Exception as rag_err:
            print(f"[WARNING] RAG query failed: {rag_err}. Proceeding without RAG context.")
            context = ""

        # 3️⃣ Call Gemini API (lightweight)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        if context:
            response = model.generate_content([prompt, f"\n\nRELEVANT PROJECT INFORMATION:\n{context}"])
        else:
            response = model.generate_content(prompt)
        
        message_body = response.text
        
        if not message_body or message_body.strip() == "":
            print(f"[ERROR] Gemini returned empty response for lead {lead.lead_name}")
            return None
        
        print(f"[GEMINI] Generated message ({len(message_body)} chars) for {lead.lead_name}")

        # 4️⃣ Save to DB for audit
        FollowUpMessage.objects.create(
            campaign=campaign,
            lead=lead,
            channel=campaign.message_channel,
            message_body=message_body,
            status="generated"
        )

        return message_body
    
    except Exception as e:
        print(f"[ERROR] Failed to generate AI message for {lead.lead_name}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None



def send_campaign_message(lead, message_body, subject):
    """
    Send initial campaign message to a lead.
    This is for the first message sent as part of a campaign (no prior replies).
    """
    if not lead.email:
        print(f"No email for lead {lead.lead_name}")
        return False
    
    try:
        # Create EmailMessage for better control
        email = EmailMessage(
            subject=subject,
            body=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[lead.email],
        )
        
        # Generate Message-ID for potential threading if lead replies
        message_id = f"<campaign-{lead.id}-{__import__('time').time()}@{settings.EMAIL_HOST.replace('.', '_')}>"
        email.extra_headers = {
            'Message-ID': message_id,
        }
        
        email.send(fail_silently=False)
        print(f"✅ Campaign message sent to {lead.lead_name} ({lead.email})")
        print(f"   Subject: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send campaign message to {lead.email}: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_followup_email(lead, message_body):
    """
    Send a follow-up email with proper reply threading.
    Uses email headers (In-Reply-To, References) to maintain conversation threads.
    """
    if not lead.email:
        print(f"No email for lead {lead.lead_name}")
        return False
    
    try:
        # Get the most recent reply from the lead to thread the response
        last_reply = lead.replies.order_by('-received_at').first()
        
        # Prepare subject with "Re:" prefix if replying to a previous message
        if last_reply and last_reply.subject:
            subject = f"Re: {last_reply.subject}" if not last_reply.subject.startswith("Re:") else last_reply.subject
        else:
            subject = f"Re: Follow-up on {lead.project_name}"
        
        # Create EmailMessage for better control over headers
        email = EmailMessage(
            subject=subject,
            body=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[lead.email],
        )
        
        # Add threading headers for proper reply conversation threading
        # These headers help email clients group messages into conversation threads
        if last_reply:
            # Generate a Message-ID based on lead and reply timestamp
            message_id = f"<reply-{lead.id}-{last_reply.id}@{settings.EMAIL_HOST.replace('.', '_')}>"
            email.extra_headers = {
                'In-Reply-To': f"<msg-{lead.id}@{settings.EMAIL_HOST.replace('.', '_')}>",
                'References': f"<msg-{lead.id}@{settings.EMAIL_HOST.replace('.', '_')}>",
                'Message-ID': message_id,
            }
            print(f"[THREADING] Adding reply headers to thread with previous message")
        
        email.send(fail_silently=False)
        print(f"✅ Email sent to {lead.lead_name} ({lead.email})")
        print(f"   Subject: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {lead.email}: {e}")
        import traceback
        traceback.print_exc()
        return False
