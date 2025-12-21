# src/omniai/api/v1/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    #organization_name: Optional[str] = None  # ← Now optional

class Token(BaseModel):
    access_token: str
    token_type: str

class UserMe(BaseModel):
    id: str
    email: str
    organization_id: str