# # agent_app/ai_agent/agent_flow.py

# from agent_app.ai_agent.intent_service import detect_intent_gemini
# from agent_app.message_service import generate_message, send_followup_email
# from agent_app.models import Lead, FollowUpMessage

# # Use modern LangGraph agent import
# # from langgraph.agents import LLMChainAgent

# def run_agent_flow(lead_id):
#     """
#     LangGraph agent workflow:
#     1. Detect intent of customer reply
#     2a. If auto_reply → generate AI message → save → send email
#     2b. If notify_agent → mark for human follow-up
#     """

#     lead = Lead.objects.get(id=lead_id)

#     # Get campaign info (last campaign)
#     campaigns = lead.campaigns.all()
#     campaign = campaigns.last() if campaigns else None

#     # Step 1: Detect intent
#     last_reply = lead.replies.order_by('-received_at').first()
#     if not last_reply:
#         print(f"⚠️ No replies found for {lead.lead_name}")
#         return

#     customer_message = last_reply.body
#     intent = detect_intent_gemini(customer_message, lead.last_conversation_summary or "")

#     # Step 2: Perform action based on intent
#     if intent == "auto_reply":
#         message_body = generate_message(lead, campaign)
#         send_followup_email(lead, message_body)
#     elif intent == "notify_agent":
#         # Example: mark lead_status or create a notification
#         lead.lead_status = "Action Required: Contact Lead"
#         lead.save()

# # Example usage
# if __name__ == "__main__":
#     test_lead_id = 1  # Replace with a valid lead ID in your DB
#     run_agent_flow(test_lead_id)



from agent_app.ai_agent.intent_service import detect_intent_gemini
from agent_app.message_service import generate_message, send_followup_email
from agent_app.models import Lead, FollowUpMessage

class Node:
    def __init__(self, name):
        self.name = name

class Edge:
    def __init__(self, src, dest, label=None):
        self.src = src
        self.dest = dest
        self.label = label

class LLMChainAgent:
    def __init__(self, nodes=None, edges=None):
        self.nodes = nodes or []
        self.edges = edges or []

    def run(self, input_text):
        # Simply return the input, simulating processing
        return input_text

# Create a dummy graph (optional, for demonstration)
nodes = [Node("DetectIntent"), Node("GenerateMessage"), Node("SendEmail")]
edges = [Edge(nodes[0], nodes[1]), Edge(nodes[1], nodes[2])]
agent = LLMChainAgent(nodes, edges)

def run_agent_flow(lead_id):
    """
    LangGraph agent workflow (dummy):
    1. Detect intent of customer reply
    2a. If auto_reply → generate AI message → save → send email
    2b. If notify_agent → mark for human follow-up
    """

    lead = Lead.objects.get(id=lead_id)

    # Get campaign info (last campaign)
    campaigns = lead.campaigns.all()
    campaign = campaigns.last() if campaigns else None
    
    if not campaign:
        print(f"⚠️ No campaign found for lead {lead.lead_name}. Skipping agent flow.")
        return

    # Step 1: Detect intent
    last_reply = lead.replies.order_by('-received_at').first()
    if not last_reply:
        print(f"⚠️ No replies found for {lead.lead_name}")
        return
    
    # Check if this reply has already been processed
    if last_reply.is_processed:
        print(f"⚠️ Reply from {lead.lead_name} already processed. Skipping.")
        return

    customer_message = last_reply.body

    # Use dummy agent (simulating LangGraph)
    processed_message = agent.run(customer_message)
    intent = detect_intent_gemini(processed_message, lead.last_conversation_summary or "")

    # Step 2: Perform action based on intent
    if intent == "auto_reply":
        print(f"[AGENT] Auto-reply detected for {lead.lead_name}. Generating AI message...")
        message_body = generate_message(lead, campaign)
        if message_body:
            sent = send_followup_email(lead, message_body)
            if sent:
                print(f"[AGENT] Auto-reply sent to {lead.lead_name}")
        else:
            print(f"[ERROR] Failed to generate message for auto-reply to {lead.lead_name}")
    elif intent == "notify_agent":
        print(f"[AGENT] Human follow-up required for {lead.lead_name}. Marking for agent.")
        # Example: mark lead_status or create a notification
        lead.lead_status = "Action Required: Contact Lead"
        lead.save()
    else:
        print(f"[WARNING] Unknown intent '{intent}' for {lead.lead_name}")
    
    # Mark reply as processed
    last_reply.is_processed = True
    last_reply.save()
    print(f"[AGENT] Marked reply as processed for {lead.lead_name}")

# Example usage
if __name__ == "__main__":
    test_lead_id = 1  # Replace with a valid lead ID in your DB
    run_agent_flow(test_lead_id)
