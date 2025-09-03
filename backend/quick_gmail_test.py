#!/usr/bin/env python3
"""
Simple Gmail app password verification
"""

import smtplib
from email.mime.text import MIMEText


def quick_test():
    try:
        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        # Try to authenticate with your app password
        server.login("r39132@gmail.com", "twpb rdzd oljn deey")

        # Create a simple test message
        msg = MIMEText("Your Gmail app password is working! 🎉")
        msg["Subject"] = "App Password Test Success"
        msg["From"] = "r39132@gmail.com"
        msg["To"] = "r39132@gmail.com"

        # Send the email
        server.send_message(msg)
        server.quit()

        print("✅ SUCCESS: App password works and email sent!")
        print("📧 Check your Gmail inbox for the test email")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ AUTHENTICATION FAILED")
        print("🔧 Your app password is incorrect or expired")
        print("📋 Steps to fix:")
        print("   1. Go to Google Account → Security → 2-Step Verification")
        print("   2. Click 'App passwords'")
        print("   3. Generate new password for 'Mail'")
        print("   4. Update your .env file with the new password")
        return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Gmail App Password...")
    print("=" * 40)
    quick_test()
