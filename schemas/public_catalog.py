from pydantic import BaseModel


class PublicBusinessInfo(BaseModel):
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


class PublicStaffInfo(BaseModel):
    slug: str
    name: str
    title: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    service_slugs: list[str]


class PublicServiceInfo(BaseModel):
    slug: str
    name: str
    duration_minutes: int
    price_amount: int
    price_currency: str


class PublicBookingRules(BaseModel):
    slot_step_minutes: int
    max_advance_days: int
    default_staff_slug: str


class PublicCatalogResponse(BaseModel):
    business: PublicBusinessInfo
    staff: list[PublicStaffInfo]
    services: list[PublicServiceInfo]
    booking_rules: PublicBookingRules
