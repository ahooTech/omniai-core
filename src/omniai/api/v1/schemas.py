# src/omniai/api/v1/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserMe(BaseModel):
    id: str
    email: str
    default_organization_id: str