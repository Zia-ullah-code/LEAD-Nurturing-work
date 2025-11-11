# import os
# import django
# import sys


# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # 1️⃣ Setup Django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_backend.settings")
# django.setup()
import sys
import os

# Add project root to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_backend.settings")
django.setup()

# ✅ Correct import of your Vanna code
from ai_agent.t2sql_tool import run_sql_query, generate_sql_from_natural_language

# Test queries
queries = [
    "How many leads are there?",
    "List leads with status Connected",
    "Show all campaigns",
    "What is the average budget?",
]

for q in queries:
    print("\n" + "="*60)
    print(f"Natural language query: {q}")

    sql = generate_sql_from_natural_language(q)
    print(f"Generated SQL: {sql}")

    result = run_sql_query(q)
    print(f"Query result:\n{result}")
