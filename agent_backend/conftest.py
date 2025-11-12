"""
Pytest configuration and fixtures for agent backend tests.
"""
import os
import sys
import django
import pytest
from django.test import Client
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import tempfile
import shutil

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_backend.settings")
django.setup()

from agent_app.models import Lead, Campaign, CampaignLead, MessageLog, LeadReply, FollowUpMessage


@pytest.fixture(scope="session")
def django_db_setup():
    """Configure test database."""
    from django.conf import settings
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }


@pytest.fixture
def api_client():
    """Django test client for API testing."""
    return Client()


@pytest.fixture
def sample_lead(db):
    """Create a sample lead for testing."""
    return Lead.objects.create(
        lead_id="L1",
        lead_name="John Doe",
        email="john.doe@example.com",
        country_code="+1",
        phone="1234567890",
        project_name="Lumina Grand",
        unit_type="2 bed",
        min_budget=500000.0,
        max_budget=800000.0,
        lead_status="Connected",
        last_conversation_date=datetime.now().date() - timedelta(days=30),
        last_conversation_summary="Interested in 2-bedroom units with good amenities."
    )


@pytest.fixture
def sample_leads(db):
    """Create multiple sample leads for testing."""
    leads = []
    for i in range(5):
        lead = Lead.objects.create(
            lead_id=f"L{i+1}",
            lead_name=f"Lead {i+1}",
            email=f"lead{i+1}@example.com",
            country_code="+1",
            phone=f"123456789{i}",
            project_name=["Lumina Grand", "Sobha Crest", "DLF West Park"][i % 3],
            unit_type=["1 bed", "2 bed", "3 bed"][i % 3],
            min_budget=400000.0 + (i * 100000),
            max_budget=700000.0 + (i * 100000),
            lead_status=["Not Connected", "Connected", "Visit scheduled"][i % 3],
            last_conversation_date=datetime.now().date() - timedelta(days=i * 10),
            last_conversation_summary=f"Sample conversation summary {i+1}"
        )
        leads.append(lead)
    return leads


@pytest.fixture
def sample_campaign(db, sample_leads):
    """Create a sample campaign with leads."""
    campaign = Campaign.objects.create(
        project_name="Sobha Crest",
        message_channel="Email",
        sales_offer="Special discount: 10% off for early buyers"
    )
    campaign.leads.set(sample_leads)
    
    # Create CampaignLead entries
    for lead in sample_leads:
        CampaignLead.objects.create(
            campaign=campaign,
            lead=lead,
            send_status="pending"
        )
    
    return campaign


@pytest.fixture
def temp_pdf_directory():
    """Create a temporary directory for PDF files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_chroma_db_path():
    """Return path to mock ChromaDB for testing."""
    return os.path.join(os.path.dirname(__file__), "test_chroma_db")


@pytest.fixture(autouse=True)
def reset_db(db):
    """Reset database before each test."""
    Lead.objects.all().delete()
    Campaign.objects.all().delete()
    CampaignLead.objects.all().delete()
    MessageLog.objects.all().delete()
    LeadReply.objects.all().delete()
    FollowUpMessage.objects.all().delete()


@pytest.fixture
def authenticated_client(db):
    """Create an authenticated test client (for JWT tests if needed)."""
    client = Client()
    # Note: JWT authentication would require actual token generation
    # For now, we'll test endpoints that don't require auth
    return client

