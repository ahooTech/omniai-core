# src/omniai/api/v1/schemas.py
from pydantic import BaseModel, EmailStr, field_validator
from typing import List
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    """
    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain a special character")
        return v
    """

        
    
class Token(BaseModel):
    access_token: str
    token_type: str

class OrganizationSummary(BaseModel):
    id: str
    name: str
    slug: str
    role: str  # "owner" or "member"
    is_default: bool

class UserMe(BaseModel):
    id: str
    email: str
    active_organization_id: str
    role_in_active_org: str
    organizations: List[OrganizationSummary]