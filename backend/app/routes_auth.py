from fastapi import APIRouter, HTTPException, status, Depends
from .models import RegisterRequest, LoginRequest, ForgotRequest, ResetRequest, TokenResponse
from .firestore_client import get_db
from .auth_utils import hash_password, verify_password, create_access_token, create_reset_token, decode_token
from .config import settings
from .deps import get_current_username
from email.utils import formataddr
import smtplib
from email.message import EmailMessage
from uuid import uuid4
from google.cloud import firestore

router = APIRouter(prefix="/auth", tags=["auth"])

def send_mail(to_email: str, subject: str, body: str):
    # In dev, only send real email if USE_EMAIL_IN_DEV is true AND SMTP settings are provided.
    can_send_real = bool(settings.use_email_in_dev and settings.smtp_host and settings.smtp_user)
    if not can_send_real:
        # Dev-mode: print to console
        print("=== EMAIL (DEV MODE) ===")
        print("TO:", to_email)
        print("SUBJECT:", subject)
        print(body)
        print("========================")
        return
    msg = EmailMessage()
    msg["From"] = formataddr((settings.email_from_name, settings.email_from))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as s:
        s.starttls()
        s.login(settings.smtp_user, settings.smtp_password)
        s.send_message(msg)

@router.post("/register")
def register(payload: RegisterRequest):
    db = get_db()
    if settings.require_invite:
        invite_ref = db.collection("invites").document(payload.invite_code)
        inv = invite_ref.get()
        if not inv.exists or not inv.to_dict().get("active", False):
            raise HTTPException(status_code=400, detail="Invalid invite code")
    user_ref = db.collection("users").document(payload.username)
    if user_ref.get().exists:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_ref.set({
        "email": payload.email,
        "password_hash": hash_password(payload.password),
    "created_at": firestore.SERVER_TIMESTAMP,
        "invite_code_used": payload.invite_code,
    })
    if settings.require_invite:
        invite_ref.update({
            "active": False,
            "used_by": payload.username,
            "used_email": payload.email,
            "used_at": firestore.SERVER_TIMESTAMP,
        })
    return {"ok": True, "message": "Registered. Please login."}

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
    reset_link = f"{'http://localhost:3000'}/reset?token={token}&username={payload.username}"  # frontend URL
    send_mail(payload.email, "Password Reset", f"Reset your password: {reset_link}")
    return {"ok": True}

@router.post("/test-email")
def test_email(to: str):
    # Simple test endpoint to verify mail config
    send_mail(to, "Test Email", "This is a test email from Family Tree API.")
    return {"ok": True}

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
        db.collection("invites").document(code).set({
            "active": True,
            "created_by": current_user,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
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
        }
        items.append(item)
    v = (view or "all").lower()
    if v == "redeemed":
        items = [i for i in items if not i.get("active") and i.get("used_by")]
    elif v == "unredeemed":
        items = [i for i in items if i.get("active")]
    return {"ok": True, "invites": items}

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
