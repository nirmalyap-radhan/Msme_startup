"""
MSME Profiles & Authentication API Router.
"""

from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.schemas.profiles import (
    LoginRequest,
    TokenResponse,
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
)
from apps.api.security.auth import create_access_token, hash_password, verify_password
from apps.api.security.dependencies import get_current_user, get_db
from services.scheme_ingestion.models import UserProfileModel

router = APIRouter(prefix="/profiles", tags=["Profiles & Auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_profile(
    payload: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Registers a new MSME enterprise profile and generates an access token."""
    existing = db.query(UserProfileModel).filter(UserProfileModel.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An enterprise profile with this email address already exists."
        )

    user_id = f"USR-{uuid4().hex[:8].upper()}"
    profile = UserProfileModel(
        id=user_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        enterprise_name=payload.enterprise_name,
        enterprise_class=payload.enterprise_class,
        sector=payload.sector,
        district=payload.district,
        udyam_number=payload.udyam_number,
        udyam_registered=payload.udyam_registered,
        production_status=payload.production_status,
        investment_plant_machinery=payload.investment_plant_machinery,
        annual_turnover=payload.annual_turnover,
        promoter_category=payload.promoter_category,
        promoter_gender=payload.promoter_gender,
        working_capital_loan_sanctioned=payload.working_capital_loan_sanctioned,
        annual_interest_paid=payload.annual_interest_paid,
        trademark_expenditure=payload.trademark_expenditure,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    token = create_access_token(data={"sub": profile.id, "email": profile.email, "role": profile.role})
    return TokenResponse(
        access_token=token,
        user=UserProfileResponse.model_validate(profile)
    )


@router.post("/login", response_model=TokenResponse)
def login_profile(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticates an MSME user and issues an access token."""
    user = db.query(UserProfileModel).filter(UserProfileModel.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserProfileResponse.model_validate(user)
    )


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: UserProfileModel = Depends(get_current_user)
):
    """Returns the authenticated enterprise's profile details."""
    return UserProfileResponse.model_validate(current_user)


@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user: UserProfileModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates attributes of the authenticated enterprise profile."""
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(current_user, field, val)

    db.commit()
    db.refresh(current_user)
    return UserProfileResponse.model_validate(current_user)
