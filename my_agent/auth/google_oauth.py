import os
import urllib.parse
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger("auth_server.google")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback")

def get_auth_url(state: str) -> str:
    """Builds Google OAuth consent URL with the CSRF state parameter"""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }
    encoded_params = urllib.parse.urlencode(params)
    return f"https://accounts.google.com/o/oauth2/v2/auth?{encoded_params}"

async def exchange_code(code: str) -> Dict[str, Any]:
    """Exchanges Google authorization code for tokens"""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, data=data)
        if response.status_code != 200:
            logger.error(f"Failed to exchange Google OAuth code: {response.status_code} - {response.text}")
            raise Exception(f"OAuth exchange failed: {response.status_code} - {response.text}")
        return response.json()

async def get_user_info(access_token: str) -> Dict[str, Any]:
    """Fetches user profile information using the access token"""
    url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch Google userinfo: {response.status_code} - {response.text}")
            raise Exception(f"Failed to fetch user profile: {response.status_code} - {response.text}")
        return response.json()
