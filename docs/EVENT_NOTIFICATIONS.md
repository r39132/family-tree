# Event Notification Setup Guide

This guide explains how to set up automated event notifications for the Family Tree application.

## Overview

The Family Tree application now supports automated email notifications for upcoming family events (birthdays and death anniversaries). The system:

- Sends **individual emails** for each upcoming event (within 48 hours)
- Tracks sent notifications to **prevent duplicates**
- Records notification logs for debugging
- Supports user-controlled notification preferences
- **Handles late enablers**: Users who enable notifications within 6 hours of an event will still receive notifications
- **Runs every 3 hours** to ensure timely delivery for recent notification enablers

## Features

### ✅ Individual Event Notifications
- One email per event (not bulk emails)
- Personalized subject lines and content
- Separate emails for birthdays vs. remembrance days

### ✅ Duplicate Prevention
- Tracks which events have been notified about
- Uses `event_notification_logs` collection to prevent re-sending
- Safe to run the notification job multiple times

### ✅ Late Enabler Support
- Users who enable notifications within 6 hours of an event still receive notifications
- Prevents users from missing events due to late notification setup
- Tracks "recent enabler" status in notification logs

### ✅ Frequent Monitoring
- Runs every 3 hours instead of daily
- Ensures timely notifications for users who enable them close to event dates
- Better coverage for different time zones

### ✅ User Preferences
- Users can enable/disable notifications via the Events page
- Per-user, per-space notification settings
- Only sends to users who have opted in

### ✅ Comprehensive Testing
- Full test suite covering all scenarios
- Tests for failure handling, rate limiting, edge cases
- Mock email testing for safe development

## API Endpoints

### Send Notifications (Cron Job Endpoint)
```
POST /events/notifications/send-reminders
```
- Finds all upcoming events (next 48 hours)
- Sends individual emails to users with notifications enabled
- Records notification logs to prevent duplicates
- Returns count of emails sent

### Get Notification Logs (Debug/Admin)
```
GET /events/notifications/logs?limit=50
```
- Shows recent notification logs for current user's space
- Useful for debugging and monitoring
- Includes timestamps, event details, recipients

### Update Notification Settings (User Control)
```
POST /events/notifications/settings
```
- Allows users to enable/disable notifications
- Per-space settings (users can have different preferences per family space)

## Setting Up Automated Notifications

### Option 1: Cron Job (Recommended for Production)

1. **Copy the notification script:**
   ```bash
   cp scripts/send-event-notifications.sh /usr/local/bin/
   chmod +x /usr/local/bin/send-event-notifications.sh
   ```

2. **Set up environment variables:**
   ```bash
   export API_BASE_URL="https://your-family-tree-api.com"
   export ADMIN_TOKEN="your-admin-jwt-token"
   export LOG_FILE="/var/log/family-tree-notifications.log"
   ```

3. **Add to crontab (run every 3 hours):**
   ```bash
   crontab -e
   # Add this line:
   0 */3 * * * /usr/local/bin/send-event-notifications.sh
   ```

4. **Alternative: Run at specific times (every 3 hours starting at midnight):**
   ```bash
   0 0,3,6,9,12,15,18,21 * * * /usr/local/bin/send-event-notifications.sh
   ```

### Option 2: Docker Compose with Cron

Add a cron service to your `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  notifications:
    image: alpine:latest
    volumes:
      - ./scripts:/scripts
      - /var/log:/var/log
    environment:
      - API_BASE_URL=http://api:8080
      - ADMIN_TOKEN=${ADMIN_TOKEN}
    command: >
      sh -c "
        apk add --no-cache curl &&
        echo '0 */3 * * * /scripts/send-event-notifications.sh' | crontab - &&
        crond -f
      "
    depends_on:
      - api
```

### Option 3: GitHub Actions (Cloud Deployment) - **CONFIGURED**

✅ **This project is now configured to use GitHub Actions for automated notifications.**

The workflow file is located at `.github/workflows/event-notifications.yml` and provides:
- Notifications every 3 hours (0, 3, 6, 9, 12, 15, 18, 21 UTC)
- Manual triggering capability
- Dry run mode for testing
- Comprehensive error handling and logging
- Support for users who enable notifications close to event dates

**Setup Instructions:** See [GitHub Actions Notifications Setup Guide](GITHUB_ACTIONS_NOTIFICATIONS.md)

**Quick Setup:**
1. Add `API_BASE_URL` secret (your deployed API URL)
2. Add `ADMIN_TOKEN` secret (valid JWT token)
3. Test with manual trigger and dry run mode

**Manual Trigger:**
- Go to GitHub → Actions → "Send Event Notifications"
- Click "Run workflow" → Enable "Dry run mode" → "Run workflow"

### Option 4: Cloud Functions/Lambda

For cloud deployments, you can set up a serverless function that runs on a schedule:

**AWS Lambda + EventBridge:**
```python
import json
import urllib.request

def lambda_handler(event, context):
    url = "https://your-api.com/events/notifications/send-reminders"
    headers = {
        "Authorization": f"Bearer {os.environ['ADMIN_TOKEN']}",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, method='POST', headers=headers)
    response = urllib.request.urlopen(req)

    return {
        'statusCode': 200,
        'body': json.dumps(response.read().decode())
    }
```

## Configuration

### Environment Variables

- `API_BASE_URL`: Base URL of your Family Tree API
- `ADMIN_TOKEN`: JWT token with admin privileges
- `LOG_FILE`: Path for notification logs (optional)

### Notification Timing

The system looks for events happening **within the next 48 hours**. This means:

- Events tomorrow will be notified about
- Events today will be notified about
- Events in 2 days will be notified about
- Events further out will not trigger notifications

### Email Configuration

Ensure your backend has proper SMTP configuration in `.env`:

```env
USE_EMAIL_IN_DEV=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@familytree.local
EMAIL_FROM_NAME=Family Tree Admin
```

## Monitoring and Debugging

### Check Notification Logs

Use the logs endpoint to see recent notifications:

```bash
curl -H "Authorization: Bearer $TOKEN" \\
  "https://your-api.com/events/notifications/logs?limit=20"
```

### Test Notification Sending

Manually trigger notifications for testing:

```bash
curl -X POST \\
  -H "Authorization: Bearer $TOKEN" \\
  "https://your-api.com/events/notifications/send-reminders"
```

### Log Files

The cron script logs to `/var/log/family-tree-notifications.log` by default:

```bash
tail -f /var/log/family-tree-notifications.log
```

### Common Issues

1. **No emails sent:** Check that users have enabled notifications in their settings
2. **Authentication errors:** Verify ADMIN_TOKEN is valid and has proper permissions
3. **SMTP errors:** Check email configuration and Gmail app password
4. **Duplicate notifications:** The system prevents this automatically, but check logs for errors

## Testing

Run the comprehensive test suite:

```bash
cd backend
python -m pytest tests/test_event_notifications.py -v
```

Tests cover:
- Individual email sending
- Duplicate prevention
- User preference handling
- Error scenarios
- Edge cases

## Database Collections

The notification system uses these Firestore collections:

- `event_notifications`: User notification preferences
- `event_notification_logs`: Tracking sent notifications
- `members`: Source data for events
- `users`: Email addresses for recipients

## Sample Notification Emails

**Birthday Notification:**
```
Subject: 🎂 Upcoming Birthday: John Doe

Hello!

This is a reminder that John Doe's birthday is coming up:

🎂 John Doe's Birthday
📅 September 10, 2025
🎈 Turning 35 years old

Don't forget to wish them a happy birthday!

Best regards,
Family Tree
```

**Remembrance Notification:**
```
Subject: 🕊️ Remembrance Day: Jane Smith

Hello!

This is a reminder of an upcoming remembrance day:

🕊️ Jane Smith's Remembrance
📅 September 10, 2025
💝 5 years since they passed

Take a moment to remember and honor their memory.

Best regards,
Family Tree
```

This automated notification system ensures that family members never miss important events while giving users full control over their notification preferences.
