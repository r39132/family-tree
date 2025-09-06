#!/usr/bin/env python3
"""
Gmail SMTP Test Script - Verify app password works
"""

import smtplib
from email.message import EmailMessage
from email.utils import formataddr

# Your Gmail settings (from .env)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "r39132@gmail.com"
SMTP_PASSWORD = "twpb rdzd oljn deey"  # Your app password
EMAIL_FROM = "r39132@gmail.com"
EMAIL_FROM_NAME = "Family Tree Test"


def test_gmail_connection():
    """Test Gmail SMTP connection and authentication"""
    print("🔧 Testing Gmail SMTP connection...")

    try:
        # Test connection and authentication
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            print(f"✅ Connected to {SMTP_HOST}:{SMTP_PORT}")

            # Start TLS encryption
            server.starttls()
            print("✅ TLS encryption started")

            # Authenticate with app password
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("✅ Authentication successful!")

            return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("🔍 Possible issues:")
        print("   - App password is incorrect")
        print("   - 2FA not enabled on Gmail account")
        print("   - App password not generated correctly")
        return False

    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def send_test_email():
    """Send actual test email"""
    print("\n📧 Sending test email...")

    try:
        msg = EmailMessage()
        msg["From"] = formataddr((EMAIL_FROM_NAME, EMAIL_FROM))
        msg["To"] = SMTP_USER  # Send to yourself
        msg["Subject"] = "Gmail App Password Test - SUCCESS!"
        msg.set_content(
            """
🎉 Congratulations!

Your Gmail app password is working correctly!

This email was sent from your Family Tree application using:
- Gmail SMTP (smtp.gmail.com:587)
- Your app password authentication
- TLS encryption

You can now use email features in your Family Tree app, including:
- Password reset emails
- Invite emails
- Notifications

--
Family Tree Application
"""
        )

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox: {SMTP_USER}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Gmail App Password Verification")
    print("=" * 40)

    # Test 1: Connection and authentication
    auth_success = test_gmail_connection()

    if auth_success:
        # Test 2: Send actual email
        email_success = send_test_email()

        if email_success:
            print("\n🎉 All tests passed! Your Gmail app password is working correctly.")
        else:
            print("\n⚠️  Authentication works but email sending failed.")
    else:
        print("\n❌ Authentication failed. Please check your app password.")
        print("\n🔧 How to fix:")
        print("1. Go to Google Account Settings")
        print("2. Security → 2-Step Verification → App passwords")
        print("3. Generate new app password for 'Mail' application")
        print("4. Update SMTP_PASSWORD in your .env file")
