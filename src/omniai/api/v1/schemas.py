# src/omniai/api/v1/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

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