import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from google.cloud import firestore

from .auth_utils import (
    create_access_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from .config import settings
from .deps import get_current_username
from .firestore_client import get_db
from .models import (
    ForgotRequest,
    LoginRequest,
    RegisterRequest,
    ResetRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def send_mail(to_email: str, subject: str, body: str):
    print("=== EMAIL SEND ATTEMPT ===")
    print(f"TO: {to_email}")
    print(f"SUBJECT: {subject}")
    print(f"Settings - USE_EMAIL_IN_DEV: {settings.use_email_in_dev}")
    print(f"Settings - SMTP_HOST: {settings.smtp_host}")
    print(f"Settings - SMTP_USER: {settings.smtp_user}")
    print(f"Settings - EMAIL_FROM: {settings.email_from}")
    print(f"Settings - EMAIL_FROM_NAME: {settings.email_from_name}")

    # In dev, only send real email if USE_EMAIL_IN_DEV is true AND SMTP settings are provided.
    can_send_real = bool(settings.use_email_in_dev and settings.smtp_host and settings.smtp_user)
    print(f"Can send real email: {can_send_real}")

    if not can_send_real:
        # Dev-mode: print to console
        print("=== EMAIL (DEV MODE) ===")
        print("TO:", to_email)
        print("SUBJECT:", subject)
        print(body)
        print("========================")
        return

    try:
        print("Creating email message...")
        msg = EmailMessage()
        msg["From"] = formataddr((settings.email_from_name, settings.email_from))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        print(f"Email message created - From: {msg['From']}, To: {msg['To']}")

        print(f"Connecting to SMTP server: {settings.smtp_host}:{settings.smtp_port}")
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
            print("Connected to SMTP server, starting TLS...")
            s.starttls()
            print("TLS started, logging in...")
            s.login(settings.smtp_user, settings.smtp_password)
            print("Logged in successfully, sending message...")
            s.send_message(msg)
            print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        raise e


class EmailInviteRequest:
    pass


@router.post("/register")
def register(payload: RegisterRequest):
    print("=== REGISTRATION ATTEMPT ===")
    print(f"Username: {payload.username}")
    print(f"Email: {payload.email}")
    print(f"Invite code: {payload.invite_code}")

    db = get_db()

    # Check username first to return a clearer error independent of invite validity
    user_ref = db.collection("users").document(payload.username)
    if user_ref.get().exists:
        print(f"❌ Username {payload.username} already exists")
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email is already registered to another user
    print("Checking if email is already registered...")
    users_query = db.collection("users").where("email", "==", payload.email).limit(1)
    existing_users = list(users_query.stream())
    if existing_users:
        existing_username = existing_users[0].id
        print(f"❌ Email {payload.email} already registered to user: {existing_username}")
        raise HTTPException(
            status_code=400,
            detail="Email address is already registered to another user",
        )
    print("✅ Email is available")

    if settings.require_invite:
        print("Validating invite code...")
        invite_ref = db.collection("invites").document(payload.invite_code)
        inv = invite_ref.get()

        if not inv.exists:
            print(f"❌ Invite code {payload.invite_code} does not exist")
            raise HTTPException(status_code=400, detail="Invalid invite code")

        invite_data = inv.to_dict()
        print(f"Invite data: {invite_data}")

        if not invite_data.get("active", False):
            print(f"❌ Invite code {payload.invite_code} is not active")
            # Check if it was already used
            if invite_data.get("used_by") or invite_data.get("used_at"):
                used_by = invite_data.get("used_by", "unknown user")
                used_at = invite_data.get("used_at", "unknown time")
                print(f"Invite was already used by: {used_by} at {used_at}")
                raise HTTPException(
                    status_code=400,
                    detail="Registration is not permitted with this token as it has already been redeemed. If you have already registered, please proceed to the login page.",
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid invite code")

        print("✅ Invite code is valid and active")

    print("Creating user account...")
    user_ref.set(
        {
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "created_at": firestore.SERVER_TIMESTAMP,
            "invite_code_used": payload.invite_code,
        }
    )
    print(f"✅ User {payload.username} created successfully")

    if settings.require_invite:
        print("Marking invite as used...")
        invite_ref.update(
            {
                "active": False,
                "used_by": payload.username,
                "used_email": payload.email,
                "used_at": firestore.SERVER_TIMESTAMP,
                "redeemed_at": firestore.SERVER_TIMESTAMP,  # New field for tracking redemption date
            }
        )
        print("✅ Invite marked as used")

    return {"ok": True, "message": "Registered. Please login."}


@router.get("/invites/{code}/validate")
def validate_invite(code: str):
    """Validate an invite code and return its status for frontend use"""
    print("=== VALIDATING INVITE CODE ===")
    print(f"Invite code: {code}")

    db = get_db()
    invite_ref = db.collection("invites").document(code)
    inv = invite_ref.get()

    if not inv.exists:
        print(f"❌ Invite code {code} does not exist")
        return {
            "valid": False,
            "error": "invalid_code",
            "message": "Invalid invite code",
        }

    invite_data = inv.to_dict()
    print(f"Invite data: {invite_data}")

    if not invite_data.get("active", False):
        print(f"❌ Invite code {code} is not active")
        # Check if it was already used
        if invite_data.get("used_by") or invite_data.get("used_at"):
            used_by = invite_data.get("used_by", "unknown user")
            used_at = invite_data.get("used_at")
            print(f"Invite was already used by: {used_by} at {used_at}")
            return {
                "valid": False,
                "error": "already_redeemed",
                "message": "Registration is not permitted with this token as it has already been redeemed. If you have already registered, please proceed to the login page.",
                "used_by": used_by,
                "used_at": str(used_at) if used_at else None,
            }
        else:
            return {
                "valid": False,
                "error": "inactive",
                "message": "This invite is no longer active",
            }

    print("✅ Invite code is valid and active")
    return {
        "valid": True,
        "message": "Invite code is valid",
        "sent_email": invite_data.get("sent_email"),
        "created_at": (
            str(invite_data.get("created_at")) if invite_data.get("created_at") else None
        ),
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    db = get_db()
    user = db.collection("users").document(payload.username).get()
    if not user.exists:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    data = user.to_dict()
    if not verify_password(payload.password, data.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(payload.username)
    return TokenResponse(access_token=token)


@router.get("/me")
def get_current_user(current_user: str = Depends(get_current_username)):
    """Get current user information."""
    db = get_db()
    user_doc = db.collection("users").document(current_user).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = user_doc.to_dict()
    return {
        "username": current_user,
        "email": data.get("email"),
        "created_at": data.get("created_at"),
    }


@router.post("/forgot")
def forgot(payload: ForgotRequest):
    db = get_db()
    doc = db.collection("users").document(payload.username).get()
    if not doc.exists:
        # Do not reveal existence
        return {"ok": True}
    data = doc.to_dict()
    if data.get("email") != payload.email:
        return {"ok": True}
    token = create_reset_token(payload.username)
    reset_link = (
        f"{'http://localhost:3000'}/reset?token={token}&username={payload.username}"  # frontend URL
    )
    send_mail(payload.email, "Password Reset", f"Reset your password: {reset_link}")
    return {"ok": True}


@router.post("/test-email")
def test_email(to: str):
    print("=== TEST EMAIL ENDPOINT CALLED ===")
    print(f"Target email: {to}")

    try:
        # Simple test endpoint to verify mail config
        send_mail(to, "Test Email", "This is a test email from Family Tree API.")
        print(f"✅ Test email endpoint completed successfully for {to}")
        return {"ok": True, "message": f"Test email sent to {to}"}
    except Exception as e:
        print(f"❌ Test email endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")


@router.post("/invite")
def create_invite(count: int = 1, current_user: str = Depends(get_current_username)):
    if not settings.require_invite:
        raise HTTPException(status_code=400, detail="Invites are disabled")
    db = get_db()
    if count < 1 or count > 10:
        raise HTTPException(status_code=400, detail="count must be between 1 and 10")
    codes = []
    for _ in range(count):
        code = str(uuid4())
        db.collection("invites").document(code).set(
            {
                "active": True,
                "created_by": current_user,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        codes.append(code)
    return {"ok": True, "invite_codes": codes}


@router.get("/invites")
def list_invites(view: str = "all", current_user: str = Depends(get_current_username)):
    db = get_db()
    docs = db.collection("invites").stream()
    items = []
    for d in docs:
        data = d.to_dict() or {}
        item = {
            "code": d.id,
            "active": data.get("active", False),
            "created_by": data.get("created_by"),
            "created_at": data.get("created_at"),
            "used_by": data.get("used_by"),
            "used_email": data.get("used_email"),
            "used_at": data.get("used_at"),
            "sent_email": data.get("sent_email"),
            "sent_at": data.get("sent_at"),
        }
        items.append(item)
    v = (view or "all").lower()
    if v == "redeemed":
        items = [i for i in items if not i.get("active") and i.get("used_by")]
    elif v == "available":
        # active and not yet emailed
        items = [i for i in items if i.get("active") and not i.get("sent_email")]
    elif v in ("invite-sent", "invitesent", "sent"):
        # active and email was sent
        items = [i for i in items if i.get("active") and i.get("sent_email")]
    return {"ok": True, "invites": items}


@router.delete("/invites/{code}")
def delete_invite(code: str, current_user: str = Depends(get_current_username)):
    """Delete an unredeemed invite token."""
    db = get_db()
    ref = db.collection("invites").document(code)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Invite not found")

    data = doc.to_dict() or {}
    # Prevent deletion of redeemed invites
    if not data.get("active", False):
        raise HTTPException(status_code=400, detail="Cannot delete redeemed invite")

    # Delete the invite document
    ref.delete()
    return {"ok": True, "message": "Invite deleted successfully"}


@router.post("/invites/{code}/email")
def email_invite_link(code: str, payload: dict, current_user: str = Depends(get_current_username)):
    """Send a registration link via email for an unredeemed invite token (authenticated version)."""
    print("=== AUTHENTICATED EMAIL INVITE SEND ===")
    print(f"Invite code: {code}")
    print(f"Current user: {current_user}")
    print(f"Payload: {payload}")

    to_email = payload.get("email")
    if not to_email:
        print("❌ No email provided in payload")
        raise HTTPException(status_code=400, detail="email is required")

    print(f"Target email: {to_email}")

    db = get_db()

    # Check if email already belongs to a registered user
    print("Checking if email already belongs to a registered user...")
    users_query = db.collection("users").where("email", "==", to_email).limit(1)
    existing_users = list(users_query.stream())
    if existing_users:
        username = existing_users[0].id
        print(f"❌ Email {to_email} already belongs to user: {username}")
        raise HTTPException(
            status_code=400,
            detail=f"Email address {to_email} is already registered to an existing user. Please use a different email address.",
        )
    print("✅ Email is not registered to any existing user")

    ref = db.collection("invites").document(code)
    doc = ref.get()
    if not doc.exists:
        print(f"❌ Invite {code} not found")
        raise HTTPException(status_code=404, detail="Invite not found")

    data = doc.to_dict() or {}
    print(f"Invite data: {data}")

    if not data.get("active", False):
        print(f"❌ Invite {code} is not active")
        raise HTTPException(status_code=400, detail="Invite has already been redeemed")

    register_link = f"{settings.frontend_url}/register?invite={code}"
    print(f"Registration link: {register_link}")

    body = (
        "You're invited to join Family Tree!\n\n"
        f"Use this link to register: {register_link}\n\n"
        "If you didn't expect this, you can ignore this email."
    )

    try:
        print("Calling send_mail for authenticated invite...")
        send_mail(to_email, "Your Family Tree invitation", body)
        print("✅ Invite email sent successfully")

        # Record that an invite email was sent
        print("Updating invite record with email send info...")
        ref.update(
            {
                "sent_email": to_email,
                "sent_at": firestore.SERVER_TIMESTAMP,
                "invited_at": firestore.SERVER_TIMESTAMP,  # New field for tracking invite sent date
            }
        )
        print("✅ Invite record updated successfully")

        return {"ok": True, "sent_email": to_email}
    except Exception as e:
        print(f"❌ Failed to send authenticated invite email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/public/invites/{code}/email")
def public_email_invite_link(code: str, payload: dict):
    """Send a registration link via email for an unredeemed invite token (public version)."""
    print("=== PUBLIC EMAIL INVITE SEND ===")
    print(f"Invite code: {code}")
    print(f"Payload: {payload}")

    to_email = payload.get("email")
    if not to_email:
        print("❌ No email provided in payload")
        raise HTTPException(status_code=400, detail="email is required")

    print(f"Target email: {to_email}")

    db = get_db()

    # Check if email already belongs to a registered user
    print("Checking if email already belongs to a registered user...")
    users_query = db.collection("users").where("email", "==", to_email).limit(1)
    existing_users = list(users_query.stream())
    if existing_users:
        username = existing_users[0].id
        print(f"❌ Email {to_email} already belongs to user: {username}")
        raise HTTPException(
            status_code=400,
            detail=f"Email address {to_email} is already registered to an existing user. Please use a different email address.",
        )
    print("✅ Email is not registered to any existing user")

    ref = db.collection("invites").document(code)
    doc = ref.get()
    if not doc.exists:
        print(f"❌ Public invite {code} not found")
        raise HTTPException(status_code=404, detail="Invite not found")

    data = doc.to_dict() or {}
    print(f"Invite data: {data}")

    if not data.get("active", False):
        print(f"❌ Public invite {code} is not active")
        raise HTTPException(status_code=400, detail="Invite has already been redeemed")

    # Basic rate limiting: check if email was sent recently (within last hour)
    sent_at = data.get("sent_at")
    if sent_at:
        print(f"Checking rate limiting - last sent at: {sent_at}")

        from datetime import datetime, timedelta, timezone

        # Convert Firestore timestamp to datetime
        if hasattr(sent_at, "seconds"):
            sent_datetime = datetime.fromtimestamp(sent_at.seconds, tz=timezone.utc)
        else:
            sent_datetime = sent_at

        time_diff = datetime.now(tz=timezone.utc) - sent_datetime
        print(f"Time since last send: {time_diff}")

        if time_diff < timedelta(hours=1):
            print(f"❌ Rate limit hit - email sent {time_diff} ago")
            raise HTTPException(
                status_code=429,
                detail="Email was sent recently. Please wait before sending again.",
            )

    register_link = f"{settings.frontend_url}/register?invite={code}"
    print(f"Registration link: {register_link}")

    body = (
        "You're invited to join Family Tree!\n\n"
        f"Use this link to register: {register_link}\n\n"
        "If you didn't expect this, you can ignore this email."
    )

    try:
        print("Calling send_mail for public invite...")
        send_mail(to_email, "Your Family Tree invitation", body)
        print("✅ Public invite email sent successfully")

        # Record that an invite email was sent
        print("Updating public invite record with email send info...")
        ref.update(
            {
                "sent_email": to_email,
                "sent_at": firestore.SERVER_TIMESTAMP,
                "invited_at": firestore.SERVER_TIMESTAMP,  # New field for tracking invite sent date
            }
        )
        print("✅ Public invite record updated successfully")

        return {"ok": True, "sent_email": to_email}
    except Exception as e:
        print(f"❌ Failed to send public invite email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/reset")
def reset(payload: ResetRequest):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    try:
        data = decode_token(payload.token)
        if data.get("kind") != "reset" or data.get("sub") != payload.username:
            raise ValueError("bad token")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    db = get_db()
    ref = db.collection("users").document(payload.username)
    if not ref.get().exists:
        raise HTTPException(status_code=400, detail="User not found")
    ref.update({"password_hash": hash_password(payload.new_password)})
    return {"ok": True}
