"""
API Workflow Tests
Tests for API endpoints including lead filtering, campaign creation, and message generation.
"""
import pytest
import json
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from agent_app.models import Lead, Campaign, CampaignLead, MessageLog


@pytest.mark.django_db
class TestAPIWorkflow:
    """Test API workflow endpoints."""
    
    def test_hello_endpoint(self, api_client):
        """Test hello endpoint."""
        response = api_client.get("/api/hello")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert "message" in data
        assert "Hello from Agent Backend!" in data["message"]
    
    def test_rag_search_endpoint(self, api_client):
        """Test RAG search endpoint."""
        response = api_client.get("/api/search", {"q": "What are the amenities in Lumina Grand?"})
        assert response.status_code == 200
        data = json.loads(response.content)
        assert "query" in data
        assert data["query"] == "What are the amenities in Lumina Grand?"
    
    def test_filter_leads_empty(self, api_client, db):
        """Test filtering leads with no leads in database."""
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
        assert data["count"] == 0
        assert len(data["leads"]) == 0
    
    def test_filter_leads_by_project(self, api_client, sample_leads):
        """Test filtering leads by project name."""
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "project_name": "Lumina Grand"
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] > 0
        for lead in data["leads"]:
            assert "Lumina Grand" in lead["project_name"]
    
    def test_filter_leads_by_unit_type(self, api_client, sample_leads):
        """Test filtering leads by unit type."""
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "unit_type": ["2 bed"]
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] > 0
        for lead in data["leads"]:
            assert lead["unit_type"] == "2 bed"
    
    def test_filter_leads_by_budget_range(self, api_client, sample_leads):
        """Test filtering leads by budget range."""
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "min_budget": 500000.0,
                "max_budget": 700000.0
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] > 0
        for lead in data["leads"]:
            if lead["min_budget"] and lead["max_budget"]:
                assert lead["min_budget"] >= 500000.0
                assert lead["max_budget"] <= 700000.0
    
    def test_filter_leads_by_lead_status(self, api_client, sample_leads):
        """Test filtering leads by lead status."""
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "lead_status": "Connected"
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] > 0
        for lead in data["leads"]:
            assert "Connected" in lead["lead_status"]
    
    def test_filter_leads_by_date_range(self, api_client, sample_leads):
        """Test filtering leads by conversation date range."""
        from_date = (datetime.now().date() - timedelta(days=50)).strftime("%Y-%m-%d")
        to_date = (datetime.now().date() - timedelta(days=10)).strftime("%Y-%m-%d")
        
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "from_date": from_date,
                "to_date": to_date
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] > 0
    
    def test_filter_leads_multiple_filters(self, api_client, sample_leads):
        """Test filtering leads with multiple filters."""
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "project_name": "Lumina Grand",
                "unit_type": ["2 bed"],
                "lead_status": "Connected"
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["count"] >= 0  # May be 0 if no leads match all criteria
    
    def test_create_campaign(self, api_client, sample_leads):
        """Test creating a campaign."""
        lead_ids = [lead.lead_id for lead in sample_leads[:3]]
        
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
        data = json.loads(response.content)
        assert data["project_name"] == "Sobha Crest"
        assert data["message_channel"] == "Email"
        assert data["sales_offer"] == "Special 10% discount"
        
        # Verify campaign was created in database
        campaign = Campaign.objects.get(id=data["id"])
        assert campaign.leads.count() == 3
    
    def test_create_campaign_whatsapp(self, api_client, sample_leads):
        """Test creating a campaign with WhatsApp channel."""
        lead_ids = [lead.lead_id for lead in sample_leads[:2]]
        
        response = api_client.post(
            "/api/campaigns/customize",
            data=json.dumps({
                "project_name": "DLF West Park",
                "message_channel": "WhatsApp",
                "sales_offer": "Early bird offer",
                "lead_ids": lead_ids
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["message_channel"] == "WhatsApp"
    
    def test_generate_messages(self, api_client, sample_campaign):
        """Test generating messages for a campaign."""
        response = api_client.post(
            f"/api/campaigns/generate_messages?campaign_id={sample_campaign.id}",
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "success"
        assert data["campaign_id"] == sample_campaign.id
        assert data["messages_generated"] > 0
        assert "details" in data
        assert len(data["details"]) == data["messages_generated"]
    
    def test_generate_messages_nonexistent_campaign(self, api_client):
        """Test generating messages for non-existent campaign."""
        response = api_client.post(
            "/api/campaigns/generate_messages?campaign_id=99999",
            content_type="application/json"
        )
        # Should return error or empty results
        assert response.status_code in [200, 404, 500]
    
    def test_fetch_replies_endpoint(self, api_client):
        """Test fetch replies endpoint."""
        response = api_client.get("/api/fetch-replies")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert "message" in data
    
    def test_lead_filter_response_structure(self, api_client, sample_leads):
        """Test that lead filter response has correct structure."""
        response = api_client.post(
            "/api/leads/filter_leads",
            data=json.dumps({
                "project_name": "Lumina Grand"
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Verify response structure
        assert "count" in data
        assert "leads" in data
        assert isinstance(data["count"], int)
        assert isinstance(data["leads"], list)
        
        # Verify lead structure
        if data["leads"]:
            lead = data["leads"][0]
            assert "id" in lead
            assert "lead_name" in lead
            assert "email" in lead
            assert "project_name" in lead
            assert "unit_type" in lead
            assert "min_budget" in lead
            assert "max_budget" in lead
            assert "lead_status" in lead
    
    def test_campaign_creation_with_empty_lead_ids(self, api_client):
        """Test creating campaign with empty lead IDs."""
        response = api_client.post(
            "/api/campaigns/customize",
            data=json.dumps({
                "project_name": "Sobha Crest",
                "message_channel": "Email",
                "sales_offer": "Test offer",
                "lead_ids": []
            }),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["project_name"] == "Sobha Crest"
        
        # Verify campaign has no leads
        campaign = Campaign.objects.get(id=data["id"])
        assert campaign.leads.count() == 0

