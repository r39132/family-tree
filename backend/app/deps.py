from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth_utils import decode_token
from .firestore_client import get_db

security = HTTPBearer(auto_error=False)


def _parse_timestamp(value) -> Optional[datetime]:
    """Parse various timestamp shapes into aware datetime in UTC."""
    if value is None:
        return None
    # Firestore Timestamp
    if hasattr(value, "seconds"):
        return datetime.fromtimestamp(value.seconds, tz=timezone.utc)
    # Python datetime
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    # Numeric epoch seconds
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    # String (ISO8601)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return None


def get_current_username(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    try:
        payload = decode_token(credentials.credentials)
        username: Optional[str] = payload.get("sub") if payload else None
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Load user
        db = get_db()
        doc = db.collection("users").document(username).get()
        if not doc.exists:
            raise HTTPException(status_code=401, detail="User not found")
        data = doc.to_dict() or {}

        # Eviction: token iat must be after sessions_invalid_after
        iat_dt = _parse_timestamp(payload.get("iat"))
        cutoff_dt = _parse_timestamp(data.get("sessions_invalid_after"))
        if cutoff_dt and iat_dt:
            if iat_dt < cutoff_dt:
                raise HTTPException(status_code=401, detail="Session expired; please login again")
        elif cutoff_dt and not iat_dt:
            # Be safe if we can't parse iat
            raise HTTPException(status_code=401, detail="Session invalid; please login again")

        return username
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
