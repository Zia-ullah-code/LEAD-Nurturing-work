"""
Text-to-SQL using Vanna
"""
import vanna as vn
from vanna.remote import VannaDefault
import os
import sys

# Add path for ChromaDB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../../ragImplementation/chroma_db"))

# Initialize Vanna (using remote for simplicity, can switch to local)
# For MVP, we'll use a simple SQL generation approach
vn_api_key = os.getenv("VANNA_API_KEY", "")
vn_model = os.getenv("VANNA_MODEL", "")

# If Vanna API not available, use simple SQL generation
USE_VANNA_API = bool(vn_api_key and vn_model)

if USE_VANNA_API:
    vn = VannaDefault(model=vn_model, api_key=vn_api_key)
else:
    # Fallback: Simple SQL generation for MVP
    vn = None


def get_db_schema():
    """Return database schema information"""
    return """
    Tables:
    - lead: lead_id, lead_name, email, project_name, unit_type, min_budget, max_budget, lead_status, last_conversation_date
    - campaign: id, project_name, message_channel, sales_offer, created_at
    - campaignlead: campaign_id, lead_id, send_status, sent_at, goal_status, proposed_datetime
    - messagelog: campaign_id, lead_id, direction, subject, body, timestamp
    - leadreply: lead_id, subject, body, received_at, is_processed
    """


def generate_sql_from_natural_language(query: str) -> str:
    """Generate SQL from natural language query"""
    query_lower = query.lower()
    
    # Simple pattern matching for MVP
    if "how many leads" in query_lower or "count leads" in query_lower:
        if "campaign" in query_lower:
            return "SELECT COUNT(*) FROM agent_app_campaignlead"
        return "SELECT COUNT(*) FROM agent_app_lead"
    
    if "list leads" in query_lower or "show leads" in query_lower:
        if "status" in query_lower:
            if "connected" in query_lower:
                return "SELECT * FROM agent_app_lead WHERE lead_status = 'Connected'"
            elif "not connected" in query_lower:
                return "SELECT * FROM agent_app_lead WHERE lead_status = 'Not Connected'"
        return "SELECT * FROM agent_app_lead LIMIT 50"
    
    if "campaigns" in query_lower:
        if "count" in query_lower or "how many" in query_lower:
            return "SELECT COUNT(*) FROM agent_app_campaign"
        return "SELECT * FROM agent_app_campaign ORDER BY created_at DESC"
    
    if "budget" in query_lower:
        if "average" in query_lower:
            return "SELECT AVG(min_budget) as avg_min, AVG(max_budget) as avg_max FROM agent_app_lead WHERE min_budget IS NOT NULL"
        if "max" in query_lower or "highest" in query_lower:
            return "SELECT MAX(max_budget) FROM agent_app_lead WHERE max_budget IS NOT NULL"
        if "min" in query_lower or "lowest" in query_lower:
            return "SELECT MIN(min_budget) FROM agent_app_lead WHERE min_budget IS NOT NULL"
    
    if "messages sent" in query_lower or "sent messages" in query_lower:
        return "SELECT COUNT(*) FROM agent_app_campaignlead WHERE send_status = 'sent'"
    
    if "goals" in query_lower or "visits" in query_lower:
        return "SELECT COUNT(*) FROM agent_app_campaignlead WHERE goal_status IS NOT NULL AND goal_status != ''"
    
    # Default: return a simple query
    return "SELECT * FROM agent_app_lead LIMIT 10"


def run_sql_query(natural_language_query: str) -> str:
    """Execute a natural language query and return results"""
    from django.db import connection
    
    try:
        if USE_VANNA_API and vn:
            # Use Vanna to generate SQL
            sql = vn.generate_sql(natural_language_query)
        else:
            # Use simple pattern matching
            sql = generate_sql_from_natural_language(natural_language_query)
        
        # Execute SQL
        with connection.cursor() as cursor:
            cursor.execute(sql)
            
            # Get column names
            columns = [col[0] for col in cursor.description] if cursor.description else []
            
            # Get results
            rows = cursor.fetchall()
            
            # Format results
            if not rows:
                return "No results found."
            
            # Convert to readable format
            result_lines = []
            result_lines.append(f"Query: {sql}")
            result_lines.append(f"\nResults ({len(rows)} rows):")
            result_lines.append("-" * 50)
            
            for row in rows[:20]:  # Limit to 20 rows
                if len(columns) == 1:
                    result_lines.append(str(row[0]))
                else:
                    row_dict = dict(zip(columns, row))
                    result_lines.append(str(row_dict))
            
            if len(rows) > 20:
                result_lines.append(f"\n... and {len(rows) - 20} more rows")
            
            return "\n".join(result_lines)
            
    except Exception as e:
        return f"Error executing query: {str(e)}\nGenerated SQL: {sql if 'sql' in locals() else 'N/A'}"


def train_vanna():
    """Train Vanna with DDL and examples (for future use)"""
    if not USE_VANNA_API:
        return "Vanna API not configured. Using simple SQL generation."
    
    schema = get_db_schema()
    vn.train(ddl=schema)
    
    # Add example queries
    examples = [
        ("How many leads are there?", "SELECT COUNT(*) FROM agent_app_lead"),
        ("List all campaigns", "SELECT * FROM agent_app_campaign"),
        ("Show leads with status Connected", "SELECT * FROM agent_app_lead WHERE lead_status = 'Connected'"),
    ]
    
    for question, sql in examples:
        vn.train(question=question, sql=sql)
    
    return "Vanna training completed"
