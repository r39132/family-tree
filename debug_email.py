#!/usr/bin/env python3
"""
Debug script to test email sending functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add backend directory to path and change to it first
backend_dir = "/Users/r39132/Projects/family-tree/backend"
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv()

# Now import app modules after path is set
from app.config import Settings  # noqa: E402
from app.routes_auth import send_mail  # noqa: E402


def main():
    # Load settings
    settings = Settings()

    print("=== EMAIL CONFIGURATION DEBUG ===")
    print(f"USE_EMAIL_IN_DEV: {settings.use_email_in_dev}")
    print(f"SMTP_HOST: '{settings.smtp_host}'")
    print(f"SMTP_USER: '{settings.smtp_user}'")
    print(f"SMTP_PASSWORD: {'***' if settings.smtp_password else '(empty)'}")
    print(f"EMAIL_FROM: {settings.email_from}")
    print(f"EMAIL_FROM_NAME: {settings.email_from_name}")
    print()

    # Check if real email can be sent
    can_send_real = bool(
        settings.use_email_in_dev and settings.smtp_host and settings.smtp_user
    )
    print(f"Can send real email: {can_send_real}")
    print()

    # Test sending email
    print("=== TESTING EMAIL SEND ===")
    try:
        send_mail(
            "sanand+6@gmail.com",
            "Test Email from Family Tree",
            "This is a test email sent from the Family Tree application debug script.",
        )
        print("Email function executed successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


if __name__ == "__main__":
    main()
