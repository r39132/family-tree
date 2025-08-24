from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth_utils import decode_token

security = HTTPBearer()


def get_current_username(token: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        data = decode_token(token.credentials)
        return data["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
