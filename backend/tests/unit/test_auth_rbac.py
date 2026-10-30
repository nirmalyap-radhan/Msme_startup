"""
Unit tests for Authentication and Role-Based Access Control (RBAC).
Tests PBKDF2 hashing, JWT generation/expiry/tamper resistance, and role verification.
"""

from datetime import timedelta
import pytest
from fastapi import HTTPException

from app.security.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.security.dependencies import get_current_user, require_role
from services.scheme_ingestion.models import UserProfileModel


def test_password_hashing_and_verification():
    raw_password = "SecretPassword123#!"
    hashed = hash_password(raw_password)

    # Has salt$hash format
    assert "$" in hashed
    salt, key = hashed.split("$")
    assert len(salt) == 32  # 16 bytes hex
    assert len(key) == 64   # sha256 hex

    # Verification
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_password, "corrupted_hash") is False


def test_unique_salts_for_identical_passwords():
    raw_password = "SamePassword456"
    hash1 = hash_password(raw_password)
    hash2 = hash_password(raw_password)

    assert hash1 != hash2
    assert verify_password(raw_password, hash1) is True
    assert verify_password(raw_password, hash2) is True


def test_jwt_token_creation_and_decoding():
    payload_data = {
        "sub": "USR-12345678",
        "email": "test@enterprise.odisha.gov.in",
        "role": "entrepreneur",
    }
    token = create_access_token(payload_data)
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "USR-12345678"
    assert decoded["email"] == "test@enterprise.odisha.gov.in"
    assert decoded["role"] == "entrepreneur"
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_token_expiry():
    payload_data = {"sub": "USR-EXPIRED", "role": "entrepreneur"}
    # Token expired 10 minutes ago
    expired_token = create_access_token(payload_data, expires_delta=timedelta(minutes=-10))
    decoded = decode_access_token(expired_token)
    assert decoded is None


def test_jwt_token_tampering():
    payload_data = {"sub": "USR-TAMPER", "role": "entrepreneur"}
    token = create_access_token(payload_data)

    # Tamper with signature
    tampered_token = token[:-5] + "abcde"
    decoded = decode_access_token(tampered_token)
    assert decoded is None


def test_rbac_dependency_enforcement():
    admin_checker = require_role(["scheme_reviewer", "platform_admin"])

    # 1. Entrepreneur attempting admin action -> 403 Forbidden
    entrepreneur_user = UserProfileModel(
        id="USR-ENT-01",
        email="msme@domain.com",
        role="entrepreneur"
    )
    with pytest.raises(HTTPException) as exc_info:
        admin_checker(user=entrepreneur_user)
    assert exc_info.value.status_code == 403
    assert "lacks required permissions" in exc_info.value.detail

    # 2. Reviewer attempting admin action -> Authorized
    reviewer_user = UserProfileModel(
        id="USR-REV-01",
        email="reviewer@msme.odisha.gov.in",
        role="scheme_reviewer"
    )
    authorized_user = admin_checker(user=reviewer_user)
    assert authorized_user.id == "USR-REV-01"

    # 3. Platform Admin attempting admin action -> Authorized
    admin_user = UserProfileModel(
        id="USR-ADM-01",
        email="admin@msme.odisha.gov.in",
        role="platform_admin"
    )
    authorized_admin = admin_checker(user=admin_user)
    assert authorized_admin.id == "USR-ADM-01"


def test_get_current_user_unauthorized():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(user=None)
    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail
