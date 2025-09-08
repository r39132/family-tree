# GitHub Actions Event Notifications Setup

This guide will help you configure automated event notifications using GitHub Actions for your Family Tree application.

## Overview

The GitHub Actions workflow will:
- Run every 3 hours (0, 3, 6, 9, 12, 15, 18, 21 UTC)
- Send individual email notifications for upcoming family events
- Handle users who enable notifications within 6 hours of an event
- Provide detailed job summaries and error reporting
- Allow manual triggering for testing

## Setup Instructions

### Step 1: Configure GitHub Secrets

You need to add two secrets to your GitHub repository:

1. **Go to your repository on GitHub**
2. **Click "Settings" → "Secrets and variables" → "Actions"**
3. **Click "New repository secret"**

**Add these secrets:**

**Secret 1: `API_BASE_URL`**
- Name: `API_BASE_URL`
- Value: Your deployed API URL (e.g., `https://your-family-tree-api.example.com`)

**Secret 2: `ADMIN_TOKEN`**
- Name: `ADMIN_TOKEN`
- Value: A valid JWT token with admin privileges

### Step 2: Generate Admin Token

To get an admin token, you can either:

**Option A: Use an existing admin user's token**
1. Log into your Family Tree application
2. Open browser developer tools (F12)
3. Go to Application/Storage → Local Storage
4. Copy the `token` value

**Option B: Generate a token programmatically**
```python
# Run this script to generate an admin token
import jwt
import datetime
from app.config import Settings

settings = Settings()

# Create admin token (adjust username as needed)
payload = {
    "sub": "admin",  # Your admin username
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=365)  # 1 year expiry
}

token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
print(f"Admin token: {token}")
```

### Step 3: Verify Workflow File

The workflow file should be at `.github/workflows/event-notifications.yml` and will:

- **Schedule**: Run every 3 hours
- **Manual Trigger**: Available in the Actions tab
- **Dry Run**: Option to test without sending emails
- **Late Enablers**: Handles users who enable notifications close to event dates

### Step 4: Test the Workflow

1. **Manual Test:**
   - Go to GitHub → Actions → "Send Event Notifications"
   - Click "Run workflow"
   - Enable "Dry run mode" for testing
   - Click "Run workflow"

2. **Check Results:**
   - View the job logs for detailed output
   - Check the job summary for success/failure details

### Step 5: Customize Schedule (Optional)

Edit `.github/workflows/event-notifications.yml` to change the schedule:

```yaml
on:
  schedule:
    # Examples:
    - cron: '0 */3 * * *'   # Every 3 hours (current setting)
    - cron: '0 */6 * * *'   # Every 6 hours
    - cron: '0 9,18 * * *'  # Daily at 9 AM and 6 PM UTC
    - cron: '0 9 * * 1-5'   # Weekdays only at 9 AM UTC
```

## Workflow Features

### ✅ Robust Error Handling
- API health checks before sending notifications
- Detailed error messages for common issues (401, 403, 404)
- Helpful troubleshooting information

### ✅ Comprehensive Logging
- HTTP status codes and response bodies
- Success metrics (emails sent, events processed)
- Structured job summaries

### ✅ Dry Run Mode
- Test the workflow without sending actual emails
- Verify API connectivity and authentication
- Perfect for debugging and setup verification

### ✅ Manual Triggering
- Run notifications on-demand from GitHub Actions UI
- Useful for testing or catching up on missed runs
- Optional dry run mode for safe testing

## Example Job Summary

**Successful Run:**
```
🎉 Event Notifications Sent Successfully

Summary:
📧 Emails sent: 4
📅 Events processed: 2
⏰ Time: 2025-09-08 09:00:15 UTC
🔗 API: https://your-api.com

Details:
{"ok": true, "sent": 4, "events_processed": 2}
```

**Failed Run:**
```
❌ Event Notifications Failed

Error Details:
🚨 HTTP Status: 401
⏰ Time: 2025-09-08 09:00:15 UTC
🔗 API: https://your-api.com

Response:
{"detail": "Invalid authentication credentials"}

Troubleshooting:
- Check API_BASE_URL and ADMIN_TOKEN secrets
- Verify the API is running and accessible
- Check the API logs for more details
```

## Troubleshooting

### Common Issues

**1. Authentication Errors (401/403)**
- Verify `ADMIN_TOKEN` secret is correctly set
- Check token hasn't expired
- Ensure the user has admin privileges

**2. API Not Reachable**
- Verify `API_BASE_URL` is correct and accessible
- Check if your API is running and deployed
- Ensure the `/healthz` endpoint exists

**3. No Emails Sent**
- Check that users have enabled notifications in their settings
- Verify there are upcoming events (within 48 hours)
- Check SMTP configuration in your API

**4. Workflow Not Running**
- GitHub may disable scheduled workflows in inactive repositories
- Manually trigger the workflow to reactivate it
- Check the Actions tab for any disabled workflows

### Manual Testing

Test your API endpoint directly:

```bash
# Test API health
curl https://your-api.com/healthz

# Test authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-api.com/events/notifications/send-reminders

# Test with your actual secrets
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$API_BASE_URL/events/notifications/send-reminders"
```

### Monitoring

- **GitHub Actions Tab**: View all workflow runs and their status
- **Job Summaries**: Quick overview of success/failure with metrics
- **Detailed Logs**: Step-by-step execution details
- **Email Notifications**: GitHub can notify you of workflow failures

## Security Considerations

- **Token Security**: Admin tokens have full access - store securely in GitHub secrets
- **Token Rotation**: Consider rotating admin tokens periodically
- **Least Privilege**: Use dedicated service accounts with minimal required permissions
- **Audit Logs**: Monitor the workflow runs and API access logs

## Next Steps

1. **Set up secrets** using the instructions above
2. **Test with dry run** to verify configuration
3. **Monitor first few runs** to ensure everything works correctly
4. **Customize schedule** if needed for your timezone/preferences

The automated event notifications will now run reliably in the cloud, ensuring your family members never miss important events!
