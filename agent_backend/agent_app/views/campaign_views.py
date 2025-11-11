from django.shortcuts import render, redirect
from agent_app.models import Lead, Campaign, CampaignLead, MessageLog  # Make sure models are imported
from agent_app.services.personalization import render_personalized_message
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from agent_app.import_leads import filter_leads
from agent_app.message_service import generate_message, send_campaign_message, send_followup_email

def shortlist_leads_view(request):
    print(f"[REQUEST] {request.method} /campaigns/shortlist_leads/")
    # Define dropdown lists
    projects = [
        "Altura", "Beachgate by Address", "Damac Bay by Cavalli", "DLF West Park",
        "Godrej Vistas", "Lumina Grand", "Sobha Crest", "Sobha Waves"
    ]
    unit_types = ["Studio", "1 bed", "2 bed", "2 bed w study", "3 bed", "4 bed", "Duplex", "Penthouse"]
    lead_statuses = [
        "Not Connected",
        "Connected",
        "Follow-up sent",
        "Visit requested",
        "Visit scheduled",
        "Visit done not purchased",
        "Purchased",
        "Not interested",
    ]

    # Filters dictionary for preserving user inputs
    filters = {}
    leads = []

    if request.method == "GET":
        # Render the page with empty form for user to select dropdowns
        return render(
            request,
            "campaign/shortlist_leads.html",
            {
                "leads": leads,
                "filters": filters,
                "projects": projects,
                "unit_types": unit_types,
                "lead_statuses": lead_statuses,
                "active_page": "shortlist",
            },
        )
    elif request.method == "POST":
        # Get filter values from the form
        project_name = request.POST.get("project_name")
        min_budget = request.POST.get("min_budget")
        max_budget = request.POST.get("max_budget")
        unit_types_selected = request.POST.getlist("unit_type")
        lead_statuses_selected = request.POST.getlist("lead_status")
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")

        # Enforce at least 2 filters (budget counts as one if min or max provided; date counts if either provided)
        filters_selected = 0
        if project_name:
            filters_selected += 1
        if min_budget or max_budget:
            filters_selected += 1
        if unit_types_selected:
            filters_selected += 1
        if lead_statuses_selected:
            filters_selected += 1
        if from_date or to_date:
            filters_selected += 1

        if filters_selected < 2:
            error_message = "Please select at least 2 filters before shortlisting."
            # Preserve inputs in filters dict
            if project_name:
                filters["project_name"] = project_name
            if min_budget:
                filters["min_budget"] = min_budget
            if max_budget:
                filters["max_budget"] = max_budget
            if unit_types_selected:
                filters["unit_type"] = unit_types_selected
            if lead_statuses_selected:
                filters["lead_status"] = lead_statuses_selected
            if from_date:
                filters["from_date"] = from_date
            if to_date:
                filters["to_date"] = to_date

            return render(
                request,
                "campaign/shortlist_leads.html",
                {
                    "leads": [],
                    "filters": filters,
                    "projects": projects,
                    "unit_types": unit_types,
                    "lead_statuses": lead_statuses,
                    "error_message": error_message,
                    "active_page": "shortlist",
                },
            )

        leads = filter_leads(
            project_name=project_name,
            min_budget=min_budget,
            max_budget=max_budget,
            unit_types_selected=unit_types_selected,
            lead_statuses_selected=lead_statuses_selected,
            from_date=from_date,
            to_date=to_date,
        )
        print(f"[FILTER] Found {leads.count()} matching leads")
        if project_name:
            filters["project_name"] = project_name
        if min_budget:
            filters["min_budget"] = min_budget
        if max_budget:
            filters["max_budget"] = max_budget
        if unit_types_selected:
            filters["unit_type"] = unit_types_selected
        if lead_statuses_selected:
            filters["lead_status"] = lead_statuses_selected
        if from_date and to_date:
            filters["from_date"] = from_date
            filters["to_date"] = to_date

        # Persist shortlist context in session
        try:
            request.session["shortlist"] = {
                "lead_ids": list(leads.values_list("id", flat=True)),
                "filters": filters,
            }
            request.session.modified = True
        except Exception as e:
            print(f"Failed to persist shortlist in session: {e}")

        return render(
            request,
            "campaign/shortlist_leads.html",
            {
                "leads": leads,
                "filters": filters,
                "projects": projects,
                "unit_types": unit_types,
                "lead_statuses": lead_statuses,
                "active_page": "shortlist",
            },
        )


def create_campaign_view(request):
    print(f"[REQUEST] {request.method} /campaigns/create/")
    # Use same project list for dropdown
    projects = [
        "Altura", "Beachgate by Address", "Damac Bay by Cavalli", "DLF West Park",
        "Godrej Vistas", "Lumina Grand", "Sobha Crest", "Sobha Waves"
    ]
    shortlist = request.session.get("shortlist", {})
    lead_ids = shortlist.get("lead_ids", [])
    leads_qs = Lead.objects.filter(id__in=lead_ids)
    shortlisted_count = leads_qs.count()

    if request.method == "GET":
        return render(
            request,
            "campaign/create_campaign.html",
            {
                "projects": projects,
                "shortlisted_count": shortlisted_count,
                "active_page": "create_campaign",
            },
        )

    elif request.method == "POST":
        project_name = request.POST.get("project_name")
        message_channel = request.POST.get("message_channel", "Email")
        sales_offer = request.POST.get("sales_offer", "")

        if not project_name:
            return render(
                request,
                "campaign/create_campaign.html",
                {
                    "projects": projects,
                    "shortlisted_count": shortlisted_count,
                    "error_message": "Please select a campaign project.",
                    "active_page": "create_campaign",
                },
            )

        # Create campaign and link leads (reuse existing data model)
        campaign = Campaign.objects.create(
            project_name=project_name,
            message_channel=message_channel,
            sales_offer=sales_offer,
        )
        campaign.leads.set(leads_qs)
        # Also create CampaignLead rows
        campaign_lead_objs = []
        for lead in leads_qs:
            campaign_lead_objs.append(CampaignLead(campaign=campaign, lead=lead))
        CampaignLead.objects.bulk_create(campaign_lead_objs, ignore_conflicts=True)
        print(f"[CAMPAIGN] Created campaign '{campaign.project_name}' with {shortlisted_count} leads")

        # Optionally: clear shortlist
        request.session["shortlist"] = {"lead_ids": [], "filters": {}}
        request.session.modified = True

        # Redirect to sending view
        return redirect("send_campaign", campaign_id=campaign.id)


def send_campaign_view(request, campaign_id: int):
    print(f"[REQUEST] POST /campaigns/{campaign_id}/send/ → Sending campaign messages")
    campaign = Campaign.objects.get(id=campaign_id)
    # Fetch pending campaign leads
    cl_qs = CampaignLead.objects.filter(campaign=campaign, send_status__in=["pending", "failed"])
    sent_count = 0

    for cl in cl_qs:
        # Use AI+RAG generator for hyper-personalization
        try:
            print(f"[DEBUG] Attempting to generate AI message for {cl.lead.lead_name}...")
            body = generate_message(cl.lead, campaign)
            print(f"[DEBUG] AI message generation result: {body[:100] if body else 'None'}...")
        except Exception as e:
            print(f"[ERROR] Failed to generate AI message for {cl.lead.lead_name}: {e}")
            import traceback
            traceback.print_exc()
            body = None

        # Fallback to lightweight template if AI fails
        if not body:
            print(f"[FALLBACK] Using template for {cl.lead.lead_name} (AI message was None/empty)")
            subj_fallback, body_fallback = render_personalized_message(
                lead=cl.lead,
                target_project=campaign.project_name,
                offer_text=campaign.sales_offer or "",
            )
            body = body_fallback
            subject = subj_fallback
        else:
            subject = f"{cl.lead.lead_name}, an update on {campaign.project_name}"

        cl.personalized_subject = subject
        cl.personalized_body = body or ""
        # Send (Email only for now)
        try:
            if campaign.message_channel == "Email" and cl.lead.email:
                # Use send_campaign_message for initial campaign messages
                sent_ok = send_campaign_message(cl.lead, body or "", subject)
                if sent_ok is False:
                    raise Exception("Email service returned False")
                cl.send_status = "sent"
                cl.sent_at = timezone.now()
                sent_count += 1
                # update lead status to reflect outbound follow-up
                try:
                    cl.lead.lead_status = "Follow-up sent"
                    cl.lead.save()
                except Exception:
                    pass
                print(f"[SENT] Email to {cl.lead.lead_name} ({cl.lead.email})")
                MessageLog.objects.create(
                    campaign=campaign,
                    lead=cl.lead,
                    direction="outbound",
                    subject=subject,
                    body=body,
                )
            else:
                cl.send_status = "failed"
        except Exception as e:
            print(f"[ERROR] Failed sending to {cl.lead.email}: {e}")
            cl.send_status = "failed"
        cl.save()

    return render(
        request,
        "campaign/create_campaign.html",
        {
            "projects": [
                "Altura", "Beachgate by Address", "Damac Bay by Cavalli", "DLF West Park",
                "Godrej Vistas", "Lumina Grand", "Sobha Crest", "Sobha Waves"
            ],
            "shortlisted_count": CampaignLead.objects.filter(campaign=campaign).count(),
            "success_message": f"Messages sent: {sent_count}",
            "active_page": "create_campaign",
        },
    )
    print(f"[COMPLETE] Campaign send finished: {sent_count} messages sent")


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def email_webhook_view(request):
    """
    Demo webhook to record inbound replies.
    Accepts JSON: { "campaign_id": int, "lead_id": int, "subject": str, "body": str }
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    try:
        import json
        payload = json.loads(request.body.decode("utf-8"))
        campaign_id = payload.get("campaign_id")
        lead_id = payload.get("lead_id")
        subject = payload.get("subject", "")
        body = payload.get("body", "")
        campaign = Campaign.objects.get(id=campaign_id)
        lead = Lead.objects.get(id=lead_id)
        MessageLog.objects.create(
            campaign=campaign,
            lead=lead,
            direction="inbound",
            subject=subject,
            body=body,
        )
        # Update CampaignLead last_reply_at
        CampaignLead.objects.filter(campaign=campaign, lead=lead).update(last_reply_at=timezone.now())
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def campaign_dashboard_view(request):
    print(f"[REQUEST] GET /campaigns/dashboard/")
    # Campaign selector
    campaigns = Campaign.objects.all().order_by("-created_at")
    selected_id = request.GET.get("campaign_id")
    selected_campaign = None
    if selected_id:
        try:
            selected_campaign = campaigns.get(id=selected_id)
        except Campaign.DoesNotExist:
            selected_campaign = None
    if not selected_campaign:
        selected_campaign = campaigns.first()

    shortlisted = 0
    messages_sent = 0
    unique_replies = 0
    goals_achieved = 0
    followups = []
    goals_list = []
    threads_by_lead = {}

    if selected_campaign:
        shortlisted = CampaignLead.objects.filter(campaign=selected_campaign).count()
        messages_sent = CampaignLead.objects.filter(campaign=selected_campaign, sent_at__isnull=False).count()
        # distinct leads with inbound messages
        inbound_qs = MessageLog.objects.filter(campaign=selected_campaign, direction="inbound")
        unique_replies = inbound_qs.values("lead_id").distinct().count()
        goals_achieved = CampaignLead.objects.filter(campaign=selected_campaign).exclude(goal_status__isnull=True).exclude(goal_status="").count()

        # Build followups list and threads
        leads_with_replies = Lead.objects.filter(message_logs__campaign=selected_campaign, message_logs__direction="inbound").distinct()
        followup_threads = []
        for lead in leads_with_replies:
            logs = list(MessageLog.objects.filter(campaign=selected_campaign, lead=lead).order_by("timestamp"))
            followups.append(lead)
            followup_threads.append({"lead": lead, "logs": logs})

        # Goals section: any campaign lead with goal_status
        goals_list = CampaignLead.objects.filter(campaign=selected_campaign).exclude(goal_status__isnull=True).exclude(goal_status="").select_related("lead")

    return render(
        request,
        "campaign/dashboard.html",
        {
            "campaigns": campaigns,
            "selected_campaign": selected_campaign,
            "metrics": {
                "shortlisted": shortlisted,
                "messages_sent": messages_sent,
                "unique_replies": unique_replies,
                "goals_achieved": goals_achieved,
            },
            "followups": followups,
            "followup_threads": followup_threads if selected_campaign else [],
            "goals_list": goals_list,
            "active_page": "dashboard",
        },
    )


def property_visits_view(request):
    print(f"[REQUEST] GET /campaigns/visits/")
    # list all viewing/call requests, most recent first
    visits = CampaignLead.objects.exclude(goal_status__isnull=True).exclude(goal_status="").select_related("lead", "campaign").order_by("-last_reply_at", "-id")
    # Build threads and last conversation summary (last outbound message snippet)
    visits_data = []
    for cl in visits:
        logs = list(MessageLog.objects.filter(campaign=cl.campaign, lead=cl.lead).order_by("timestamp"))
        last_outbound = (
            MessageLog.objects.filter(campaign=cl.campaign, lead=cl.lead, direction="outbound")
            .order_by("-timestamp")
            .first()
        )
        summary = (last_outbound.body[:160] + "…") if (last_outbound and last_outbound.body and len(last_outbound.body) > 160) else (last_outbound.body if last_outbound else "")
        visits_data.append(
            {
                "cl": cl,
                "logs": logs,
                "last_summary": summary,
            }
        )
    return render(
        request,
        "campaign/visits.html",
        {
            "visits_data": visits_data,
            "active_page": "visits",
        },
    )

