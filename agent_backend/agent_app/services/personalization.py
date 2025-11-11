from typing import Tuple
from agent_app.models import Lead


def render_personalized_message(lead: Lead, target_project: str, offer_text: str) -> Tuple[str, str]:
    """
    Lightweight personalization template using structured data + last summary.
    Returns (subject, body).
    """
    subject = f"{lead.lead_name}, a quick update on {target_project}"

    summary = lead.last_conversation_summary or ""
    unit = lead.unit_type or "your preferred unit"
    budget_min = f"{int(lead.min_budget):,}" if lead.min_budget else "-"
    budget_max = f"{int(lead.max_budget):,}" if lead.max_budget else "-"
    offer = f"\n\nLimited-time offer: {offer_text}" if offer_text else ""

    body = (
        f"Hi {lead.lead_name},\n\n"
        f"Thanks again for your interest earlier in {lead.project_name or 'our properties'}."
        f"{f' Here is a quick recap from our last conversation: {summary}' if summary else ''}\n\n"
        f"We think {target_project} could be a great fit for you"
        f" based on your preferences (unit: {unit}, budget: {budget_min} - {budget_max})."
        f"{offer}\n\n"
        f"Would you like to schedule a quick call or a property viewing?"
        f" Happy to share a few options that match your needs.\n\n"
        f"Best regards,\nSales Team"
    )

    return subject, body


