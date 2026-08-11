import os
import time
from typing import Optional

import jwt
from fastapi import Header, HTTPException
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 days

if not JWT_SECRET:
    # Fail loudly rather than silently signing tokens with a blank/default
    # secret, which would let anyone forge a valid session for any user.
    raise RuntimeError(
        "JWT_SECRET is not set. Add a long random value to your .env file "
        "(e.g. `python -c \"import secrets; print(secrets.token_hex(32))\"`)."
    )
if not GOOGLE_CLIENT_ID:
    raise RuntimeError(
        "GOOGLE_CLIENT_ID is not set. Add the OAuth Client ID from Google "
        "Cloud Console (APIs & Services > Credentials) to your .env file."
    )


class GoogleProfile:
    def __init__(self, sub: str, email: str, name: str, picture: Optional[str]):
        self.sub = sub
        self.email = email
        self.name = name
        self.picture = picture


def verify_google_credential(credential: str) -> GoogleProfile:
    """
    Verifies a Google ID token's signature against Google's public keys and
    checks it was actually issued for OUR app (the `aud` claim must match
    GOOGLE_CLIENT_ID — without this check, a token issued for a completely
    different Google app would also pass verification). Raises on any
    tampering, expiry, or audience mismatch.
    """
    try:
        idinfo = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google credential: {e}")

    return GoogleProfile(
        sub=idinfo["sub"],
        email=idinfo.get("email", ""),
        name=idinfo.get("name", idinfo.get("email", "User")),
        picture=idinfo.get("picture"),
    )


def create_session_token(profile: GoogleProfile) -> str:
    now = int(time.time())
    payload = {
        "sub": profile.sub,
        "email": profile.email,
        "name": profile.name,
        "picture": profile.picture,
        "iat": now,
        "exp": now + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please sign in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session token")


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    FastAPI dependency — add `user: dict = Depends(get_current_user)` to any
    route that needs to know who's calling. Reads the `Authorization: Bearer
    <token>` header, verifies OUR session JWT (not Google's), and returns the
    decoded payload ({sub, email, name, picture}). Raises 401 if the header
    is missing, malformed, or the token is invalid/expired — FastAPI turns
    that into a proper 401 response before the route body ever runs.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_session_token(token)