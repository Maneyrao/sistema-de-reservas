from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminServiceBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=2, max_length=120)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    duration_minutes: int = Field(..., ge=15, le=480)
    price_amount: int = Field(..., ge=0)
    price_currency: str = Field(default="ARS", pattern=r"^[A-Z]{3}$")
    active: bool = True

    @field_validator("slug")
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("duration_minutes")
    def validate_duration_step(cls, value: int) -> int:
        if value % 15 != 0:
            raise ValueError("duration_minutes must be divisible by 15")
        return value


class AdminCreateServiceRequest(AdminServiceBase):
    pass


class AdminUpdateServiceRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    duration_minutes: int | None = Field(default=None, ge=15, le=480)
    price_amount: int | None = Field(default=None, ge=0)
    price_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    active: bool | None = None

    @field_validator("slug")
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip().lower()

    @field_validator("duration_minutes")
    def validate_duration_step(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value % 15 != 0:
            raise ValueError("duration_minutes must be divisible by 15")
        return value


class AdminServiceOut(BaseModel):
    id: int
    name: str
    slug: str
    duration_minutes: int
    price_amount: int
    price_currency: str
    active: bool
