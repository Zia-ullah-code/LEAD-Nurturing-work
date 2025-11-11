from django.db import models


class Lead(models.Model):
    lead_id = models.CharField(max_length=10, null=True, blank=True)
    lead_name = models.CharField(max_length=255)
    email = models.EmailField()
    country_code = models.CharField(max_length=10, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    unit_type = models.CharField(max_length=100, null=True, blank=True)
    min_budget = models.FloatField(null=True, blank=True)
    max_budget = models.FloatField(null=True, blank=True)
    lead_status = models.CharField(max_length=100, null=True, blank=True)
    last_conversation_date = models.DateField(null=True, blank=True)
    last_conversation_summary = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.lead_name


class Campaign(models.Model):
    project_name = models.CharField(max_length=100)
    message_channel = models.CharField(
        max_length=20,
        choices=[('Email', 'Email'), ('WhatsApp', 'WhatsApp')]
    )
    sales_offer = models.TextField(blank=True, null=True)
    leads = models.ManyToManyField('Lead', related_name='campaigns')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_name} ({self.message_channel})"


class FollowUpMessage(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="messages")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20, choices=[("Email", "Email"), ("WhatsApp", "WhatsApp")])
    message_body = models.TextField()
    status = models.CharField(max_length=20, default="generated")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.lead_name} - {self.campaign.project_name}"


from django.db import models

class LeadReply(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="replies")
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Reply from {self.lead.lead_name} at {self.received_at}"


class CampaignLead(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="campaign_leads")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="campaign_memberships")
    personalized_subject = models.CharField(max_length=255, blank=True, null=True)
    personalized_body = models.TextField(blank=True, null=True)
    send_status = models.CharField(max_length=20, default="pending")  # pending | sent | failed
    sent_at = models.DateTimeField(blank=True, null=True)
    last_reply_at = models.DateTimeField(blank=True, null=True)
    goal_status = models.CharField(max_length=50, blank=True, null=True)  # e.g., viewing_scheduled
    proposed_datetime = models.DateTimeField(blank=True, null=True)
    proposed_time_text = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("campaign", "lead")

    def __str__(self):
        return f"{self.lead.lead_name} in {self.campaign.project_name}"


class MessageLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="message_logs")
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="message_logs")
    direction = models.CharField(max_length=10)  # outbound | inbound
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()
    provider_message_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.direction} to {self.lead.lead_name} at {self.timestamp}"
