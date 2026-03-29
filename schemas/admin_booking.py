from datetime import date, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminBookingListQuery(BaseModel):
    date_from: date
    date_to: date
    status: list[str] | None = None


class AdminBookingOut(BaseModel):
    id: int
    status: str
    start_datetime: str
    end_datetime: str
    customer_name: str
    customer_phone: str | None
    customer_email: EmailStr | None = None
    service_name: str
    service_slug: str
    staff_name: str
    staff_slug: str
    notes: str | None
    canceled_reason: str | None
    created_at: str


class AdminCancelBookingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str | None = Field(default=None, max_length=255)


class AdminRescheduleBookingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    new_date: date
    new_time: time
    reason: str | None = Field(default=None, max_length=255)


class AdminUpdateStatusRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    status: str
    reason: str | None = Field(default=None, max_length=255)


class AdminCustomerBookingInfo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(..., min_length=2, max_length=80)
    last_name: str = Field(..., min_length=2, max_length=80)
    phone: str = Field(..., min_length=8, max_length=40)
    email: EmailStr | None = None


class AdminCreateBookingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    staff_slug: str = Field(..., min_length=2, max_length=120)
    service_slug: str = Field(..., min_length=2, max_length=120)
    date: date
    time: time
    customer: AdminCustomerBookingInfo
    notes: str | None = Field(default=None, max_length=500)
    status: str = Field(default="confirmed", min_length=3, max_length=40)
