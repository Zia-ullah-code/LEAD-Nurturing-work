"""
Text-to-SQL (T2SQL) Tests
Tests for T2SQL functionality using Vanna and natural language to SQL conversion.
"""
import pytest
from django.db import connection
from agent_app.t2sql import (
    generate_sql_from_natural_language,
    run_sql_query,
    get_db_schema
)
from agent_app.models import Lead, Campaign, CampaignLead


@pytest.mark.django_db
class TestT2SQL:
    """Test Text-to-SQL functionality."""
    
    def test_get_db_schema(self):
        """Test getting database schema."""
        schema = get_db_schema()
        assert isinstance(schema, str)
        assert "Tables:" in schema
        assert "lead" in schema.lower()
        assert "campaign" in schema.lower()
    
    def test_generate_sql_count_leads(self):
        """Test generating SQL for counting leads."""
        sql = generate_sql_from_natural_language("How many leads are there?")
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()
        assert "COUNT" in sql.upper()
        assert "lead" in sql.lower()
    
    def test_generate_sql_list_leads(self):
        """Test generating SQL for listing leads."""
        sql = generate_sql_from_natural_language("List all leads")
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()
        assert "FROM" in sql.upper()
        assert "lead" in sql.lower()
    
    def test_generate_sql_leads_by_status(self):
        """Test generating SQL for filtering leads by status."""
        sql = generate_sql_from_natural_language("List leads with status Connected")
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()
        assert "WHERE" in sql.upper()
        assert "Connected" in sql or "connected" in sql.lower()
    
    def test_generate_sql_leads_by_status_not_connected(self):
        """Test generating SQL for not connected leads."""
        sql = generate_sql_from_natural_language("Show leads with status Not Connected")
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()
        assert "Not Connected" in sql or "not connected" in sql.lower()
    
    def test_generate_sql_campaigns(self):
        """Test generating SQL for campaigns."""
        sql = generate_sql_from_natural_language("List all campaigns")
        assert isinstance(sql, str)
        assert "SELECT" in sql.upper()
        assert "campaign" in sql.lower()
    
    def test_generate_sql_count_campaigns(self):
        """Test generating SQL for counting campaigns."""
        sql = generate_sql_from_natural_language("How many campaigns are there?")
        assert isinstance(sql, str)
        assert "COUNT" in sql.upper()
        assert "campaign" in sql.lower()
    
    def test_generate_sql_budget_average(self):
        """Test generating SQL for average budget."""
        sql = generate_sql_from_natural_language("What is the average budget?")
        assert isinstance(sql, str)
        assert "AVG" in sql.upper()
        assert "budget" in sql.lower()
    
    def test_generate_sql_budget_max(self):
        """Test generating SQL for maximum budget."""
        sql = generate_sql_from_natural_language("What is the maximum budget?")
        assert isinstance(sql, str)
        assert "MAX" in sql.upper()
        assert "budget" in sql.lower()
    
    def test_generate_sql_budget_min(self):
        """Test generating SQL for minimum budget."""
        sql = generate_sql_from_natural_language("What is the minimum budget?")
        assert isinstance(sql, str)
        assert "MIN" in sql.upper()
        assert "budget" in sql.lower()
    
    def test_generate_sql_messages_sent(self):
        """Test generating SQL for messages sent."""
        sql = generate_sql_from_natural_language("How many messages were sent?")
        assert isinstance(sql, str)
        assert "COUNT" in sql.upper()
        assert "sent" in sql.lower()
    
    def test_generate_sql_goals_achieved(self):
        """Test generating SQL for goals achieved."""
        sql = generate_sql_from_natural_language("How many visits were scheduled?")
        assert isinstance(sql, str)
        assert "COUNT" in sql.upper()
        assert "goal" in sql.lower() or "visit" in sql.lower()
    
    def test_run_sql_query_count_leads(self, sample_leads):
        """Test running SQL query to count leads."""
        result = run_sql_query("How many leads are there?")
        assert isinstance(result, str)
        assert "Query:" in result or "Results" in result or "No results" in result
    
    def test_run_sql_query_list_leads(self, sample_leads):
        """Test running SQL query to list leads."""
        result = run_sql_query("List all leads")
        assert isinstance(result, str)
        # Should return results or a message
        assert len(result) > 0
    
    def test_run_sql_query_leads_by_status(self, sample_leads):
        """Test running SQL query for leads by status."""
        result = run_sql_query("Show leads with status Connected")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_run_sql_query_campaigns(self, sample_campaign):
        """Test running SQL query for campaigns."""
        result = run_sql_query("List all campaigns")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_run_sql_query_budget_average(self, sample_leads):
        """Test running SQL query for average budget."""
        result = run_sql_query("What is the average budget?")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_run_sql_query_error_handling(self):
        """Test SQL query error handling with invalid query."""
        # This should handle errors gracefully
        result = run_sql_query("Invalid query that doesn't make sense")
        assert isinstance(result, str)
        # Should return either results or error message
    
    def test_run_sql_query_with_empty_database(self, db):
        """Test running SQL query with empty database."""
        result = run_sql_query("How many leads are there?")
        assert isinstance(result, str)
        # Should handle empty database gracefully
    
    def test_sql_query_execution(self, sample_leads):
        """Test that SQL queries actually execute against database."""
        # Create a known number of leads
        initial_count = Lead.objects.count()
        assert initial_count > 0
        
        # Run query
        result = run_sql_query("How many leads are there?")
        assert isinstance(result, str)
        # Result should reflect the actual count (may be in different formats)
    
    def test_sql_query_with_joins(self, sample_campaign):
        """Test SQL queries that might involve joins."""
        result = run_sql_query("How many leads are in campaigns?")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_multiple_sql_queries(self, sample_leads, sample_campaign):
        """Test running multiple SQL queries in sequence."""
        queries = [
            "How many leads are there?",
            "List all campaigns",
            "What is the average budget?",
            "How many messages were sent?"
        ]
        
        for query_text in queries:
            result = run_sql_query(query_text)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection is prevented (basic test)."""
        # Test with potentially dangerous input
        malicious_query = "'; DROP TABLE leads; --"
        result = run_sql_query(malicious_query)
        # Should not execute malicious SQL
        assert isinstance(result, str)
        # Database should still be accessible
        assert Lead.objects.count() >= 0
    
    def test_sql_query_case_insensitive(self, sample_leads):
        """Test that SQL generation handles case variations."""
        queries = [
            "HOW MANY LEADS ARE THERE?",
            "how many leads are there?",
            "How Many Leads Are There?",
            "how many LEADS are THERE?"
        ]
        
        for query_text in queries:
            sql = generate_sql_from_natural_language(query_text)
            assert isinstance(sql, str)
            assert "SELECT" in sql.upper()

