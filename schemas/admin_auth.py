from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    business_slug: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class AdminUserOut(BaseModel):
    id: int
    business_id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    last_login_at: datetime | None


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    admin: AdminUserOut
