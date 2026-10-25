"""
Authentication and Cryptographic Utilities.
Implements PBKDF2-HMAC-SHA256 password hashing with unique salts,
and HS256 JWT access token generation and verification.
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import jwt

from apps.api.config import api_config

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hashes a password with PBKDF2-HMAC-SHA256 using a cryptographically secure salt."""
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt$hash using constant-time comparison."""
    try:
        salt, key_hex = hashed_password.split("$")
        computed_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(computed_key.hex(), key_hex)
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=api_config.jwt_access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, api_config.app_secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT access token."""
    try:
        payload = jwt.decode(token, api_config.app_secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
