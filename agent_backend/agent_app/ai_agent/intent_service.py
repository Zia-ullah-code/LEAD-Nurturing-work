# agent_app/ai_agent/intent_service.py

import os
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyDqfiqXi1CFvWM_YlW64BCKYJnOlmfZn_o")


def detect_intent_gemini(customer_message: str, last_conversation_summary: str = "") -> str:
    """
    Uses Gemini to classify the intent of a customer reply.

    Returns:
        - "auto_reply" → AI should reply to the customer
        - "notify_agent" → Human sales agent needs to follow up
    """

    prompt = f"""
        You are an AI assistant that classifies customer responses.

        Customer reply: '{customer_message}'
        Last conversation summary: '{last_conversation_summary}'

        Task: Classify the input text from customer as auto_reply or notify_agent baed on following criterion:

        * If the customer wants to schedule a call, property viewing, or explicitly expresses readiness to buy return 'notify_agent'.
        * If the customer is asking further questions about the property or seeking information return 'auto_reply'.

        Output ONLY one of these keywords: auto_reply or notify_agent
        """

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([prompt])
    output_text = response.text.strip().lower()

    return output_text



# Example usage
if __name__ == "__main__":
    # test_msg = "Hi, I am interested in visiting the property next week."
    test_msg = "Hi, whats the pricing scheme for lumina guard."

    intent = detect_intent_gemini(test_msg)
    print(f"Detected intent: {intent}")
