from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: str           # UUID
    email: str
    name: str
    avatar_url: Optional[str]
    provider: str     # "email" | "google"
    google_id: Optional[str]
    created_at: datetime
    last_login: datetime

@dataclass
class OTPRecord:
    id: str
    email: str
    code_hash: str     # HMAC-SHA-256 hash of OTP
    expires_at: datetime
    used: bool
    attempts: int
    created_at: datetime

@dataclass
class OAuthState:
    state: str        # CSRF state token
    expires_at: datetime
