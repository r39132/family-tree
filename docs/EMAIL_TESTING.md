# Email Functionality Testing

This document describes how to test the email functionality in the Family Tree application.

## Test Coverage

The email tests cover:

1. **Send email invite** - Send initial invite email to a user
2. **Resend email invite** - Attempt to resend (tests rate limiting)
3. **Send different email invite** - Send a different invite to the same email
4. **Delete invite** - Remove an unused invite
5. **Prevent deleted invite usage** - Ensure deleted invites cannot be redeemed

## Running Tests

### Option 1: Standalone Test Script

```bash
# Make sure the backend server is running first
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# In another terminal, run the comprehensive test
cd /Users/r39132/Projects/family-tree
python test_email_functionality.py
```

### Option 2: Pytest Suite

```bash
cd backend
uv run pytest tests/test_email_functionality.py -v
```

### Option 3: Manual API Testing

```bash
# 1. Create an invite
curl -X POST "http://localhost:8080/auth/invite?count=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Send invite email
curl -X POST "http://localhost:8080/auth/invites/INVITE_CODE/email" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "r39132+2@gmail.com"}'

# 3. Try to resend (should fail due to rate limiting)
curl -X POST "http://localhost:8080/auth/public/invites/INVITE_CODE/email" \
  -H "Content-Type: application/json" \
  -d '{"email": "r39132+2@gmail.com"}'

# 4. Delete invite
curl -X DELETE "http://localhost:8080/auth/invites/INVITE_CODE" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. Try to register with deleted invite (should fail)
curl -X POST "http://localhost:8080/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass", "invite_code": "INVITE_CODE"}'
```

## Expected Results

### Successful Tests
- ✅ Server health check passes
- ✅ Authentication works
- ✅ Invite creation succeeds
- ✅ Email sending works (or shows debug output)
- ✅ Rate limiting prevents immediate resends
- ✅ Different invites can be sent to same email
- ✅ Invite deletion works
- ✅ Deleted invites cannot be redeemed

### Debug Output

With the debug logging added, you should see detailed output like:

```
=== EMAIL SEND ATTEMPT ===
TO: r39132+2@gmail.com
SUBJECT: Your Family Tree invitation
Settings - USE_EMAIL_IN_DEV: True
Settings - SMTP_HOST: smtp.gmail.com
Settings - SMTP_USER: r39132@gmail.com
Can send real email: True
Creating email message...
Email message created - From: Family Tree Admin <noreply@familytree.local>, To: r39132+2@gmail.com
Connecting to SMTP server: smtp.gmail.com:587
Connected to SMTP server, starting TLS...
TLS started, logging in...
Logged in successfully, sending message...
✅ Email sent successfully!
```

## Troubleshooting

### Common Issues

1. **Server not running**: Make sure uvicorn is running on port 8080
2. **Authentication failed**: Check if REQUIRE_INVITE is enabled
3. **SMTP errors**: Verify Gmail app password and settings
4. **Rate limiting**: Wait 1 hour between resend attempts

### Email Configuration

Ensure your `.env` file has:
```
USE_EMAIL_IN_DEV=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@familytree.local
```

## Test Email Addresses

The tests use these email patterns:
- `r39132+2@gmail.com` - Main test email
- Gmail + addressing allows multiple test emails to same inbox
