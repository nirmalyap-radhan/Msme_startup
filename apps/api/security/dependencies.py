"""
FastAPI Security & Database Dependencies.
Provides database session injection, JWT user authentication, and Role-Based Access Control (RBAC).
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api.security.auth import decode_access_token
from services.scheme_ingestion.models import UserProfileModel
from services.scheme_ingestion.storage import SchemeStorageRepository

security_bearer = HTTPBearer(auto_error=False)


def get_db():
    repo = SchemeStorageRepository()
    session = repo.get_session()
    try:
        yield session
    finally:
        session.close()


def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[UserProfileModel]:
    """Extracts the authenticated user if a valid bearer token is provided; otherwise returns None."""
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(UserProfileModel).filter(UserProfileModel.id == user_id).first()
    return user


def get_current_user(
    user: Optional[UserProfileModel] = Depends(get_current_user_optional)
) -> UserProfileModel:
    """Requires an authenticated user; raises HTTP 401 Unauthorized if missing."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    """Enforces Role-Based Access Control (RBAC). Raises HTTP 403 Forbidden if role unauthorized."""
    def role_checker(user: UserProfileModel = Depends(get_current_user)) -> UserProfileModel:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{user.role}' lacks required permissions: {allowed_roles}.",
            )
        return user
    return role_checker
