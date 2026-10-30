"""
Pydantic API Schemas for User Profiles and Authentication.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "entrepreneur"  # entrepreneur, facilitator, scheme_reviewer
    enterprise_name: Optional[str] = None
    enterprise_class: Optional[str] = None  # micro, small, medium
    sector: Optional[str] = None
    district: Optional[str] = None
    udyam_number: Optional[str] = None
    udyam_registered: bool = False
    production_status: str = "commenced"
    investment_plant_machinery: Optional[float] = None
    annual_turnover: Optional[float] = None
    promoter_category: str = "general"
    promoter_gender: str = "male"
    working_capital_loan_sanctioned: Optional[float] = None
    annual_interest_paid: Optional[float] = None
    trademark_expenditure: Optional[float] = None


class UserProfileUpdate(BaseModel):
    enterprise_name: Optional[str] = None
    enterprise_class: Optional[str] = None
    sector: Optional[str] = None
    district: Optional[str] = None
    udyam_number: Optional[str] = None
    udyam_registered: Optional[bool] = None
    production_status: Optional[str] = None
    investment_plant_machinery: Optional[float] = None
    annual_turnover: Optional[float] = None
    promoter_category: Optional[str] = None
    promoter_gender: Optional[str] = None
    working_capital_loan_sanctioned: Optional[float] = None
    annual_interest_paid: Optional[float] = None
    trademark_expenditure: Optional[float] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    role: str
    enterprise_name: Optional[str] = None
    enterprise_class: Optional[str] = None
    sector: Optional[str] = None
    state: str = "Odisha"
    district: Optional[str] = None
    udyam_number: Optional[str] = None
    udyam_registered: bool = False
    production_status: str = "commenced"
    investment_plant_machinery: Optional[float] = None
    annual_turnover: Optional[float] = None
    promoter_category: str = "general"
    promoter_gender: str = "male"
    working_capital_loan_sanctioned: Optional[float] = None
    annual_interest_paid: Optional[float] = None
    trademark_expenditure: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse
