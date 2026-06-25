import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-fallback-super-secret-key-32-chars-at-least-2026")
ALGORITHM = "HS256"
EXPIRE_HOURS = 24

class InvalidTokenError(Exception):
    pass

class TokenExpiredError(Exception):
    pass

def create_token(user_id: str, email: str, name: str, provider: str, avatar_url: Optional[str] = None) -> str:
    expire = datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "provider": provider,
        "avatar_url": avatar_url,
        "exp": expire
    }
    encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    try:
        # jwt.decode automatically verifies expiration time
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError:
        raise InvalidTokenError("Invalid token signature or payload")

def decode_token_no_verify(token: str) -> Dict[str, Any]:
    """Helper to inspect payload on the client/debugging side without validating signature"""
    try:
        payload = jwt.get_unverified_claims(token)
        return payload
    except JWTError:
        raise InvalidTokenError("Unable to decode token")
