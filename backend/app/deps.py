from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth_utils import decode_token

security = HTTPBearer(auto_error=False)


def get_current_username(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    try:
        data = decode_token(credentials.credentials)
        return data["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
