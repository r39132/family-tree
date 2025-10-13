import datetime as dt
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from .config import settings
from .utils.time import utc_now

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bcrypt has a 72-byte limit, so we truncate passwords to this length
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    # Truncate password to 72 bytes to comply with bcrypt limits
    password_bytes = password.encode("utf-8")[:MAX_PASSWORD_BYTES]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated_password)


def verify_password(plain: str, hashed: str) -> bool:
    # Truncate password to 72 bytes to comply with bcrypt limits
    password_bytes = plain.encode("utf-8")[:MAX_PASSWORD_BYTES]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.verify(truncated_password, hashed)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    now = utc_now()
    expire = now + dt.timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    to_encode = {"sub": subject, "exp": expire, "iat": now}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_reset_token(username: str, minutes: int = 30) -> str:
    expire = utc_now() + dt.timedelta(minutes=minutes)
    return jwt.encode(
        {"sub": username, "exp": expire, "kind": "reset"},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
