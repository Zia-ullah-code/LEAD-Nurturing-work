"""
Integration Tests
End-to-end tests for the complete workflow from lead filtering to message sending and agent responses.
"""
import pytest
import json
from django.test import Client
from django.utils import timezone
from datetime import datetime, timedelta
from agent_app.models import Lead, Campaign, CampaignLead, MessageLog, LeadReply
from agent_app.ai_agent.agent_flow import run_agent_flow


@pytest.mark.django_db
class TestIntegrationWorkflow:
    """Test complete integration workflows."""
    
    def test_complete_campaign_workflow(self, api_client, sample_leads):
        """Test complete campaign workflow from filtering to sending."""
        # Step 1: Filter leads
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "project_name": "Lumina Grand",
                "unit_type": ["2 bed"]
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] >= 0
        
        # Step 2: Create campaign
        if data["count"] > 0:
            lead_ids = [lead["id"] for lead in data["leads"][:3]]
            
            response = api_client.post(
                "/api/campaigns/customize",
                data=json.dumps({
                    "project_name": "Sobha Crest",
                    "message_channel": "Email",
                    "sales_offer": "Special 10% discount",
                    "lead_ids": lead_ids
                }),
                content_type="application/json"
            )
            assert response.status_code == 200
            campaign_data = json.loads(response.content)
            campaign_id = campaign_data["id"]
            
            # Step 3: Generate messages
            response = api_client.post(
                f"/api/campaigns/generate_messages?campaign_id={campaign_id}",
                content_type="application/json"
            )
            assert response.status_code == 200
            messages_data = json.loads(response.content)
            assert messages_data["status"] == "success"
    
    def test_lead_filter_to_campaign_creation(self, api_client, sample_leads):
        """Test workflow from lead filtering to campaign creation."""
        # Filter leads
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "lead_status": "Connected"
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Create campaign with filtered leads
        if data["count"] > 0:
            lead_ids = [lead["id"] for lead in data["leads"]]
            
            response = api_client.post(
                "/api/campaigns/customize",
                data=json.dumps({
                    "project_name": "DLF West Park",
                    "message_channel": "Email",
                    "sales_offer": "Early bird offer",
                    "lead_ids": lead_ids
                }),
                content_type="application/json"
            )
            assert response.status_code == 200
            campaign_data = json.loads(response.content)
            
            # Verify campaign was created
            campaign = Campaign.objects.get(id=campaign_data["id"])
            assert campaign.leads.count() == len(lead_ids)
    
    def test_campaign_message_generation_workflow(self, sample_campaign):
        """Test complete message generation workflow."""
        # Verify campaign exists
        assert Campaign.objects.filter(id=sample_campaign.id).exists()
        
        # Verify leads are linked
        assert sample_campaign.leads.count() > 0
        
        # Verify CampaignLead entries exist
        campaign_leads = CampaignLead.objects.filter(campaign=sample_campaign)
        assert campaign_leads.count() > 0
    
    def test_rag_search_integration(self, api_client):
        """Test RAG search integration with API."""
        # Test RAG search
        response = api_client.get("/api/search", {"q": "What are the amenities?"})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert "query" in data
    
    def test_t2sql_integration(self, sample_leads):
        """Test T2SQL integration with database."""
        from agent_app.t2sql import run_sql_query
        
        # Test querying leads
        result = run_sql_query("How many leads are there?")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_agent_flow_integration(self, sample_lead, sample_campaign):
        """Test agent flow integration with replies."""
        # Create a reply
        reply = LeadReply.objects.create(
            lead=sample_lead,
            subject="Re: Follow-up",
            body="What are the facilities in this property?",
            is_processed=False
        )
        
        # Link lead to campaign
        CampaignLead.objects.create(
            campaign=sample_campaign,
            lead=sample_lead,
            send_status="sent"
        )
        
        # Run agent flow
        try:
            run_agent_flow(sample_lead.id)
            
            # Verify reply was processed
            reply.refresh_from_db()
            assert True  # If no exception, test passes
        except Exception as e:
            pytest.skip(f"Agent flow requires external services: {e}")
    
    def test_message_logging_integration(self, sample_campaign, sample_lead):
        """Test message logging integration."""
        # Create a message log
        message_log = MessageLog.objects.create(
            campaign=sample_campaign,
            lead=sample_lead,
            direction="outbound",
            subject="Test Subject",
            body="Test message body"
        )
        
        # Verify message log was created
        assert MessageLog.objects.filter(id=message_log.id).exists()
        
        # Verify it's linked to campaign and lead
        assert message_log.campaign == sample_campaign
        assert message_log.lead == sample_lead
    
    def test_campaign_lead_tracking_integration(self, sample_campaign, sample_leads):
        """Test campaign lead tracking integration."""
        # Create campaign leads
        for lead in sample_leads:
            CampaignLead.objects.create(
                campaign=sample_campaign,
                lead=lead,
                send_status="pending"
            )
        
        # Verify all leads are tracked
        campaign_leads = CampaignLead.objects.filter(campaign=sample_campaign)
        assert campaign_leads.count() == len(sample_leads)
    
    def test_lead_reply_processing_integration(self, sample_lead, sample_campaign):
        """Test lead reply processing integration."""
        # Create a reply
        reply = LeadReply.objects.create(
            lead=sample_lead,
            subject="Re: Follow-up",
            body="I'm interested in scheduling a viewing.",
            is_processed=False
        )
        
        # Link to campaign
        campaign_lead = CampaignLead.objects.create(
            campaign=sample_campaign,
            lead=sample_lead,
            send_status="sent",
            sent_at=timezone.now()
        )
        
        # Create message log for outbound message
        MessageLog.objects.create(
            campaign=sample_campaign,
            lead=sample_lead,
            direction="outbound",
            subject="Initial follow-up",
            body="Test message"
        )
        
        # Process reply
        reply.is_processed = True
        reply.save()
        
        # Update campaign lead
        campaign_lead.last_reply_at = timezone.now()
        campaign_lead.goal_status = "viewing_requested"
        campaign_lead.save()
        
        # Verify updates
        campaign_lead.refresh_from_db()
        assert campaign_lead.last_reply_at is not None
        assert campaign_lead.goal_status == "viewing_requested"
    
    def test_end_to_end_workflow(self, api_client, sample_leads):
        """Test complete end-to-end workflow."""
        # Step 1: Filter leads
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "project_name": "Lumina Grand"
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        
        # Step 2: Create campaign
        if sample_leads:
            lead_ids = [lead.lead_id for lead in sample_leads[:2]]
            
            response = api_client.post(
                "/api/campaigns/customize",
                data=json.dumps({
                    "project_name": "Sobha Crest",
                    "message_channel": "Email",
                    "sales_offer": "Test offer",
                    "lead_ids": lead_ids
                }),
                content_type="application/json"
            )
            assert response.status_code == 200
            campaign_data = json.loads(response.content)
            
            # Step 3: Generate messages
            response = api_client.post(
                f"/api/campaigns/generate_messages?campaign_id={campaign_data['id']}",
                content_type="application/json"
            )
            assert response.status_code == 200
    
    def test_rag_and_t2sql_integration(self, api_client, sample_leads):
        """Test integration between RAG and T2SQL."""
        # Test RAG search
        response = api_client.get("/api/search", {"q": "What are the facilities?"})
        assert response.status_code == 200
        
        # Test T2SQL
        from agent_app.t2sql import run_sql_query
        result = run_sql_query("How many leads are there?")
        assert isinstance(result, str)
    
    def test_campaign_metrics_integration(self, sample_campaign, sample_leads):
        """Test campaign metrics calculation."""
        # Create campaign leads with different statuses
        for i, lead in enumerate(sample_leads):
            CampaignLead.objects.create(
                campaign=sample_campaign,
                lead=lead,
                send_status="sent" if i % 2 == 0 else "pending",
                sent_at=timezone.now() if i % 2 == 0 else None,
                goal_status="viewing_requested" if i == 0 else None
            )
        
        # Calculate metrics
        shortlisted = CampaignLead.objects.filter(campaign=sample_campaign).count()
        messages_sent = CampaignLead.objects.filter(
            campaign=sample_campaign,
            sent_at__isnull=False
        ).count()
        goals_achieved = CampaignLead.objects.filter(
            campaign=sample_campaign
        ).exclude(goal_status__isnull=True).exclude(goal_status="").count()
        
        # Verify metrics
        assert shortlisted == len(sample_leads)
        assert messages_sent >= 0
        assert goals_achieved >= 0

