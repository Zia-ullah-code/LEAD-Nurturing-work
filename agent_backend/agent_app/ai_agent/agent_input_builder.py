from agent_app.models import Lead, Campaign, LeadReply

def build_agent_input(lead_id: int):
    lead = Lead.objects.get(id=lead_id)
    campaigns = lead.campaigns.all()  # leads can belong to multiple campaigns
    
    # Get last campaign
    campaign = campaigns.last()
    
    # Get last conversation summary
    last_summary = lead.last_conversation_summary or ""
    
    # Get latest customer reply (email/whatsapp)
    last_reply = lead.replies.order_by('-received_at').first()
    customer_message = last_reply.body if last_reply else ""
    
    # Build input dict
    input_data = {
        "lead_name": lead.lead_name,
        "campaign_name": campaign.project_name if campaign else "",
        "campaign_offer": campaign.sales_offer if campaign else "",
        "last_conversation_summary": last_summary,
        "customer_message": customer_message,
    }
    
    return input_data
