# agent_backend/urls.py
from django.contrib import admin
from django.urls import path
from agent_app.api import api  # <-- this works only if api = NinjaAPI() exists

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("api/", api.urls),  # exposes your Ninja routes
#     path("campaigns/send_messages/", send_messages, name="send_messages"),

# ]


from django.contrib import admin
from django.urls import path
from agent_app.api import api
from agent_app.views.campaign_views import shortlist_leads_view, create_campaign_view, send_campaign_view, email_webhook_view, campaign_dashboard_view, property_visits_view  # 👈 import this
# from agent_app.views.email_views import send_messages  # 👈 (you already have this)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),  # Ninja API endpoints
    # path("campaigns/shortlist_leads/", shortlist_leads_view, name="shortlist_leads"),
    path("campaigns/shortlist_leads/", shortlist_leads_view, name="shortlist_leads"),
    path("campaigns/create/", create_campaign_view, name="create_campaign"),
    path("campaigns/<int:campaign_id>/send/", send_campaign_view, name="send_campaign"),
    path("webhooks/email/", email_webhook_view, name="email_webhook"),
    path("campaigns/dashboard/", campaign_dashboard_view, name="campaign_dashboard"),
    path("campaigns/visits/", property_visits_view, name="property_visits"),

    # path("campaigns/send_messages/", send_messages, name="send_messages"),

]
