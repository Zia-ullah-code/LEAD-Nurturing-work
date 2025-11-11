
import imaplib
import email
import os
from email.header import decode_header
from django.utils import timezone
from agent_app.models import Lead, FollowUpMessage, LeadReply, CampaignLead, MessageLog, Campaign
from agent_app.ai_agent.agent_flow import run_agent_flow
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

# Gmail IMAP settings (use app password)
EMAIL = "laybaa.fiaz@gmail.com"
PASSWORD = "niwk tnqb yaec sryf"
IMAP_SERVER = "imap.gmail.com"


def _detect_goal_intent(text: str) -> str:
    """
    Very simple intent detector. Returns a goal_status string or "".
    """
    if not text:
        return ""
    lower = text.lower()
    if any(k in lower for k in ["schedule a viewing", "property viewing", "book a tour", "visit", "site visit"]):
        return "viewing_requested"
    if any(k in lower for k in ["schedule a call", "phone call", "call me", "speak on phone", "talk on phone"]):
        return "call_requested"
    if any(k in lower for k in ["proceed to buy", "ready to buy", "purchase", "book unit"]):
        return "purchase_intent"
    return ""


def fetch_lead_replies():
    print("[FETCH_REPLIES] Starting reply fetch process...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # Fetch leads who have been contacted recently (via our send flow)
    # Either have outbound MessageLog or CampaignLead.sent_at
    contacted_leads = Lead.objects.filter(
        message_logs__direction="outbound"
    ).distinct() | Lead.objects.filter(
        campaign_memberships__sent_at__isnull=False
    ).distinct()

    total_updated = 0

    for lead in contacted_leads:
        # Search for emails from this lead only
        status, data = mail.search(None, f'FROM "{lead.email}"')
        if data == [b''] or len(data[0].split()) == 0:
            continue

        message_ids = data[0].split()
        for num in message_ids[-5:]:  # last 5 emails from lead
            status, msg_data = mail.fetch(num, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decode subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            # Extract email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and part.get_payload(decode=True):
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            # Check if this reply already exists (to avoid duplicates)
            reply_exists = LeadReply.objects.filter(
                lead=lead,
                subject=subject,
                body=body
            ).exists()
            
            if reply_exists:
                print(f"[SKIP] Duplicate reply from {lead.lead_name} - already processed")
                continue

            # Save reply
            lead_reply = LeadReply.objects.create(
                lead=lead,
                subject=subject,
                body=body
            )
            print(f"[NEW] Reply from {lead.lead_name}: {subject[:50]}")

            # Update lead's last conversation info
            lead.last_conversation_summary = body[:500]
            lead.last_conversation_date = timezone.now()
            lead.save()
            total_updated += 1

            # Attach inbound MessageLog to most recent campaign that contacted this lead
            recent_cl = CampaignLead.objects.filter(lead=lead).order_by("-sent_at", "-id").first()
            if recent_cl:
                # Check if MessageLog already exists for this reply (avoid duplicates)
                msg_log_exists = MessageLog.objects.filter(
                    campaign=recent_cl.campaign,
                    lead=lead,
                    direction="inbound",
                    subject=subject,
                    body=body
                ).exists()
                
                if not msg_log_exists:
                    MessageLog.objects.create(
                        campaign=recent_cl.campaign,
                        lead=lead,
                        direction="inbound",
                        subject=subject,
                        body=body,
                    )
                    print(f"[MSGLOG] Created inbound MessageLog for {lead.lead_name}")
                
                # Update last_reply_at and optionally goal_status
                recent_cl.last_reply_at = timezone.now()
                goal = _detect_goal_intent(body)
                if goal:
                    recent_cl.goal_status = goal
                    print(f"[GOAL] Detected goal '{goal}' for {lead.lead_name}")
                    # naive proposed time extraction
                    if "tomorrow" in (body or "").lower():
                        recent_cl.proposed_datetime = timezone.now() + timedelta(days=1)
                        recent_cl.proposed_time_text = "tomorrow"
                    else:
                        # fallback to store snippet for manual follow-up
                        recent_cl.proposed_time_text = (body or "")[:120]
                    # Map goal to lead status and notify designated sales associate
                    if goal in ("viewing_requested", "call_requested"):
                        try:
                            lead.lead_status = "Visit requested"
                            lead.save()
                        except Exception:
                            pass
                    # Notify designated sales associate
                    try:
                        sales_email = getattr(settings, "DEFAULT_SALES_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
                        if sales_email:
                            notif_subject = f"[Goal detected] {lead.lead_name} — {goal.replace('_', ' ').title()}"
                            when_text = recent_cl.proposed_datetime.strftime("%b %d, %Y %H:%M") if recent_cl.proposed_datetime else (recent_cl.proposed_time_text or "-")
                            notif_body = (
                                f"Lead: {lead.lead_name} <{lead.email}>\n"
                                f"Campaign: {recent_cl.campaign.project_name}\n"
                                f"Detected Goal: {goal}\n"
                                f"Proposed Time: {when_text}\n\n"
                                f"Latest Reply Snippet:\n{(body or '')[:500]}"
                            )
                            send_mail(
                                subject=notif_subject,
                                message=notif_body,
                                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None),
                                recipient_list=[sales_email],
                                fail_silently=True,
                            )
                    except Exception as notify_err:
                        print(f"[WARNING] Failed to send goal notification: {notify_err}")
                recent_cl.save()
            else:
                print(f"[WARNING] No recent campaign found for lead {lead.lead_name}")

            # Trigger the AI agent flow for this lead
            try:
                print(f"[AGENT_FLOW] Triggering agent flow for lead {lead.lead_name}...")
                run_agent_flow(lead_id=lead.id)
            except Exception as agent_err:
                print(f"[ERROR] Agent flow failed for {lead.lead_name}: {agent_err}")
                import traceback
                traceback.print_exc()

    mail.logout()
    print(f"[FETCH_REPLIES] Complete! Processed {total_updated} new replies.")
    return total_updated


if __name__ == "__main__":
    # When running standalone, ensure Django is set up
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_backend.settings")
    import django
    django.setup()
    fetch_lead_replies()
