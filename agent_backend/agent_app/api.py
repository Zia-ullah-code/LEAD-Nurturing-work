# agent_app/api.py
from ninja import NinjaAPI
import sys, os
from ninja import NinjaAPI, Schema
from typing import Optional, List
from agent_app.models import Campaign, Lead
from django.utils import timezone
from agent_app.message_service import generate_message
from agent_app.fetch_replies import fetch_lead_replies




# --- Add ragImplementation folder to Python path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ragImplementation")))

# --- Importing RAG query function ---
from rag_main import query


# --- Importing Lead model ---
from agent_app.models import Lead


api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return {"message": "Hello from Agent Backend!"}


# -------------------------------
# 2️⃣ RAG Search Endpoint
# -------------------------------

@api.get("/search")
def search(request, q: str):
    print(f"📨 Received query via API: {q}")

    
    # Call your RAG query function
    results = query(q)
    
    # Format the results for JSON output
    response = []
    for r in results:
        response.append({
            "source": r.metadata["file_name"],
            "chunk_id": r.metadata["chunk_id"],
            "text": r.page_content
        })

    if not results:
        return {"query": q, "message": "No relevant brochures found."}

    
    return {"query": q, "results": response}




# -------------------------------
# 3️⃣ Lead Filtering Endpoint
# -------------------------------

# --- Response schema ---
class LeadOut(Schema):
    id: int
    lead_name: str
    email: str
    country_code: Optional[str]
    phone: Optional[str]
    project_name: Optional[str]
    unit_type: Optional[str]
    min_budget: Optional[float]
    max_budget: Optional[float]
    lead_status: Optional[str]
    last_conversation_date: Optional[str]
    last_conversation_summary: Optional[str]

class LeadFilterSchema(Schema):
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    project_name: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    unit_type: Optional[List[str]] = None
    lead_status: Optional[str] = None

@api.post("/leads/filter_leads")
def filter_leads(request, filters: LeadFilterSchema):
    leads = Lead.objects.all()

    # Apply filters dynamically
    if filters.from_date and filters.to_date:
        leads = leads.filter(last_conversation_date__range=[filters.from_date, filters.to_date])

    if filters.project_name:
        leads = leads.filter(project_name__icontains=filters.project_name)

    if filters.min_budget and filters.max_budget:
        leads = leads.filter(min_budget__gte=filters.min_budget, max_budget__lte=filters.max_budget)

    if filters.unit_type:
        leads = leads.filter(unit_type__in=filters.unit_type)

    if filters.lead_status:
        leads = leads.filter(lead_status__icontains=filters.lead_status)

    # Format the results
    results = [
        {
            "id": l.lead_id,
            "lead_name": l.lead_name,
            "email": l.email,
            "country_code": l.country_code,
            "phone": l.phone,
            "project_name": l.project_name,
            "unit_type": l.unit_type,
            "min_budget": l.min_budget,
            "max_budget": l.max_budget,
            "lead_status": l.lead_status,
            "last_conversation_date": l.last_conversation_date.strftime("%Y-%m-%d") if l.last_conversation_date else None,
            "last_conversation_summary": l.last_conversation_summary,
        }
        for l in leads
    ]

    # Return both leads and count
    return {
        "count": len(results),
        "leads": results
    }



class CampaignIn(Schema):
    project_name: str
    message_channel: str   # "Email" or "WhatsApp"
    sales_offer: str = ""
    lead_ids: List[str]    # accepts ["L1", "L2", ...]



from datetime import datetime

class CampaignOut(Schema):
    id: int
    project_name: str
    message_channel: str
    sales_offer: str
    created_at: datetime



@api.post("/campaigns/customize", response=CampaignOut)
def create_campaign(request, data: CampaignIn):
    # Create campaign record
    campaign = Campaign.objects.create(
        project_name=data.project_name,
        message_channel=data.message_channel,
        sales_offer=data.sales_offer,
        created_at=timezone.now()
    )

    # Link leads using your custom field
    leads = Lead.objects.filter(lead_id__in=data.lead_ids)
    campaign.leads.set(leads)

    return campaign



# -------------------------------
# 4 deafting messages Endpoint
# -------------------------------



@api.post("/campaigns/generate_messages")
def send_messages(request, campaign_id: int):
    campaign = Campaign.objects.get(id=campaign_id)
    leads = campaign.leads.all()

    generated = []
    for lead in leads:
        message_body = generate_message(lead, campaign)
        generated.append({
            "lead_id": lead.lead_id,
            "lead_name": lead.lead_name,
            "email": lead.email,
            "message_preview": message_body[:120]
        })

    return {
        "status": "success",
        "campaign_id": campaign.id,
        "messages_generated": len(generated),
        "details": generated
    }


from agent_app.models import Campaign, FollowUpMessage
from agent_app.message_service import send_followup_email

@api.post("/send_messages/{campaign_id}")
def send_messages(request, campaign_id: int):
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        messages = FollowUpMessage.objects.filter(campaign=campaign,lead__email="laybafiaz.trainee@devsinc.com", status="generated")

        results = []
        for msg in messages:
            sent = send_followup_email(msg.lead, msg.message_body)
            msg.status = "sent" if sent else "failed"
            msg.save()

            results.append({
                "lead": msg.lead.lead_name,
                "email": msg.lead.email,
                "status": msg.status,
            })

        return {
            "status": "success",
            "messages_sent": len(results),
            "details": results
        }

    except Campaign.DoesNotExist:
        return {"status": "error", "message": "Campaign not found"}



@api.get("/fetch-replies")
def get_replies(request):
    print("[REQUEST] GET /api/fetch-replies → Fetching email replies")
    updated = fetch_lead_replies()
    print(f"[COMPLETE] Fetched replies: {updated} leads updated")
    return {"message": "Fetched new replies successfully"}