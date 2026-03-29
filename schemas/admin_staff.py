from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminAvailabilityRuleIn(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time

    @field_validator("end_time")
    def validate_range(cls, value: time, info) -> time:
        start_time = info.data.get("start_time")
        if start_time is not None and value <= start_time:
            raise ValueError("end_time must be greater than start_time")
        return value


class AdminAvailabilityRuleOut(AdminAvailabilityRuleIn):
    id: int


class AdminAssignedServiceOut(BaseModel):
    id: int
    name: str
    slug: str
    duration_minutes: int
    price_amount: int
    price_currency: str
    active: bool


class AdminCreateStaffRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=2, max_length=120)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    title: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
    active: bool = True
    service_ids: list[int] = Field(default_factory=list)
    availability_rules: list[AdminAvailabilityRuleIn] = Field(default_factory=list)

    @field_validator("slug")
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()


class AdminUpdateStaffRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    title: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
    active: bool | None = None
    service_ids: list[int] | None = None
    availability_rules: list[AdminAvailabilityRuleIn] | None = None

    @field_validator("slug")
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().lower()


class AdminStaffOut(BaseModel):
    id: int
    name: str
    slug: str
    title: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    active: bool
    services: list[AdminAssignedServiceOut]
    availability_rules: list[AdminAvailabilityRuleOut]
