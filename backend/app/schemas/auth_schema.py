# backend/app/schemas/auth_schema.py
from datetime import datetime
from typing import Optional

from pydantic import EmailStr

from app.schemas.common_schema import CamelModel


class TokenExchangeRequest(CamelModel):
    code: str


class UserResponse(CamelModel):
    id: str
    name: str
    email: EmailStr
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    created_at: datetime


class AccessTokenResponse(CamelModel):
    access_token: str
    user: UserResponse