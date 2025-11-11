# Email Threading Implementation - Complete Guide

## Problem Solved
Previously, when the agent sent auto-reply messages to leads, they were being sent as **new standalone emails** instead of **replies** to the lead's original messages. This meant:
- Messages didn't appear in the same conversation thread
- The UI couldn't group related messages together
- Email clients showed them as separate conversations

## Solution Implemented

### 1. **Email Headers for Threading**
We now add proper SMTP headers to enable email threading:

```
In-Reply-To: <msg-{lead.id}@mail_host>
References: <msg-{lead.id}@mail_host>
Message-ID: <reply-{lead.id}-{reply.id}@mail_host>
```

These headers tell email clients (Gmail, Outlook, etc.) to group the message in the same conversation thread.

### 2. **Two Types of Email Functions**

#### `send_campaign_message(lead, message_body, subject)`
- **Used for**: Initial campaign messages (first contact with lead)
- **Subject**: Custom subject (e.g., "Aminah, A Perfect Match for Godrej Vistas")
- **Threading**: Generates a unique Message-ID for future replies to reference
- **Location**: `message_service.py`

```python
def send_campaign_message(lead, message_body, subject):
    """Send initial campaign message to a lead."""
    # Generates Message-ID for future threading
    email.extra_headers = {
        'Message-ID': message_id,
    }
```

#### `send_followup_email(lead, message_body)`
- **Used for**: Auto-reply messages to lead replies
- **Subject**: "Re: {original_subject}" (automatic reply prefix)
- **Threading**: Includes In-Reply-To and References headers
- **Location**: `message_service.py`

```python
def send_followup_email(lead, message_body):
    """Send auto-reply with proper threading headers."""
    if last_reply:
        email.extra_headers = {
            'In-Reply-To': f"<msg-{lead.id}@...>",
            'References': f"<msg-{lead.id}@...>",
            'Message-ID': message_id,
        }
```

### 3. **Files Modified**

| File | Changes |
|------|---------|
| `message_service.py` | Added LeadReply import, created `send_campaign_message()`, updated `send_followup_email()` with threading headers |
| `email_service.py` | Updated `send_followup_email()` with threading headers |
| `campaign_views.py` | Imported `send_campaign_message`, now uses it for initial messages |
| `agent_flow.py` | Already correctly uses `send_followup_email()` for auto-replies (no changes needed) |
| `api.py` | Updated import to use `send_followup_email` from `message_service` |

### 4. **Flow Diagram**

```
Lead Receives Initial Campaign Message
    ↓
[send_campaign_message()]
    ├─ Custom subject
    ├─ Message-ID header set
    └─ Email stored in MessageLog (outbound)
    
    ↓
Lead Replies to Email
    ↓
[fetch_replies.py]
    ├─ Fetches reply from Gmail IMAP
    ├─ Creates LeadReply record
    ├─ Creates MessageLog (inbound) ← Same thread now!
    ├─ Detects intent (goal)
    └─ Calls run_agent_flow()
    
    ↓
[agent_flow.py → run_agent_flow()]
    ├─ Checks if reply already processed
    ├─ Detects intent: "auto_reply" vs "notify_agent"
    └─ If auto_reply:
        ├─ Generates AI message
        └─ [send_followup_email()] ← Uses In-Reply-To headers
            ├─ References original message
            ├─ Same thread as lead's reply
            └─ Email stored in MessageLog (outbound)
            
    ↓
Dashboard View
    └─ Shows thread with both messages in same conversation
```

### 5. **Email Client Behavior**

When lead receives auto-reply:
- **Gmail**: Shows in same conversation thread ✅
- **Outlook**: Shows in same conversation thread ✅
- **Apple Mail**: Shows in same thread ✅

Without these headers:
- Messages appear as separate conversations ❌
- Can't see context of full exchange ❌

## Testing the Implementation

### Test Case 1: Initial Campaign Message
```
1. Create campaign and send to lead
2. Verify: Message shows in lead's email as new message
3. Expected: Subject = "Aminah, A Perfect Match for Godrej Vistas"
```

### Test Case 2: Auto-Reply
```
1. Lead replies to campaign message
2. System fetches reply (fetch_replies.py)
3. Agent generates auto-reply
4. Verify: Auto-reply appears in SAME thread in email client
5. Expected: Subject = "Re: Aminah, A Perfect Match for Godrej Vistas"
```

### Test Case 3: Multiple Exchanges
```
1. Campaign → Lead (initial)
2. Lead → Agent (reply)
3. Agent → Lead (auto-reply)
4. Lead → Agent (another reply)
5. Agent → Lead (second auto-reply)
6. Verify: All in one thread
```

## Key Features

✅ **Automatic Threading**: Email clients automatically group messages
✅ **Proper Subjects**: "Re:" prefix added automatically
✅ **Fallback Support**: Works with or without lead's previous reply
✅ **Subject Preservation**: Keeps original subject in thread
✅ **Error Handling**: Graceful fallback if threading fails
✅ **Logging**: Clear debug messages about threading

## Configuration Required

No additional configuration needed - the system uses:
- `settings.EMAIL_HOST` (for domain)
- `settings.DEFAULT_FROM_EMAIL` (sender)
- `settings.EMAIL_HOST_USER` (for domain extraction)

## Future Improvements

1. **Gmail Labels**: Add custom labels to group conversations
2. **Conversation Summary**: Show last few messages in preview
3. **Smart Routing**: Auto-route to appropriate sales agent based on goal
4. **Reply Delay**: Add delay before auto-reply for natural feel

## Troubleshooting

**Issue**: Auto-reply not showing in thread
- **Solution**: Verify email headers in MessageLog
- **Debug**: Check `settings.EMAIL_HOST` is set correctly

**Issue**: Subject not showing "Re:"
- **Solution**: Verify `last_reply.subject` exists
- **Debug**: Check LeadReply records are created

**Issue**: Email not threaded in Gmail
- **Solution**: Clear Gmail cache or restart email client
- **Note**: Threading can take a few seconds to appear

