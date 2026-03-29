from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminBusinessOut(BaseModel):
    id: int
    slug: str
    name: str
    timezone: str
    tagline: str | None = None
    hero_title: str | None = None
    hero_description: str | None = None
    announcement: str | None = None
    booking_note: str | None = None
    address: str | None = None
    phone: str | None = None
    instagram_url: str | None = None
    maps_url: str | None = None


class AdminUpdateBusinessRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    tagline: str | None = Field(default=None, max_length=255)
    hero_title: str | None = Field(default=None, max_length=255)
    hero_description: str | None = Field(default=None, max_length=1000)
    announcement: str | None = Field(default=None, max_length=255)
    booking_note: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    instagram_url: str | None = Field(default=None, max_length=255)
    maps_url: str | None = Field(default=None, max_length=500)

    @field_validator("phone")
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) < 8:
            raise ValueError("Phone must contain at least 8 digits")
        return value
