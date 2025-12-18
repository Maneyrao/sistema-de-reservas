# schemas/booking.py

from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import date, time, datetime,timedelta
from typing import Optional, Literal

class CustomerInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[0-9\s\-()]+$')

class SlotInfo(BaseModel):
    date: date
    start_time: time
    end_time: time
    start_datetime: datetime
    end_datetime: datetime

class PriceInfo(BaseModel):
    amount: int = Field(..., ge=0)
    currency: str = Field(..., pattern=r'^[A-Z]{3}$')

class ServiceInfo(BaseModel):
    slug: str
    name: str
    duration_minutes: int
    price: PriceInfo

class StaffInfo(BaseModel):
    slug: str
    name: str

class BusinessInfo(BaseModel):
    slug: str
    name: str

class CancellationPolicy(BaseModel):
    can_cancel_until: datetime
    min_hours_before: int

class BookingCreate(BaseModel):
    service_slug: str
    staff_slug: str
    date: date
    time: time
    customer: CustomerInfo
    notes: Optional[str] = Field(None, max_length=500)
    validation_token: Optional[str] = None
    
    @field_validator('date')
    def validate_date_range(cls, v):
        today = date.today()
        max_date = today + timedelta(days=30)
        
        if v < today:
            raise ValueError("No se puede reservar en el pasado")
        if v > max_date:
            raise ValueError("No se puede reservar con más de 30 días de anticipación")
        
        return v

class BookingResponse(BaseModel):
    code: str
    status: Literal["pending", "confirmed", "cancelled", "completed", "no_show"]
    business: BusinessInfo
    service: ServiceInfo
    staff: StaffInfo
    slot: SlotInfo
    customer: CustomerInfo
    notes: Optional[str]
    created_at: datetime
    cancellation_policy: CancellationPolicy
    
    class Config:
        from_attributes = True

class BookingCancel(BaseModel):
    email: EmailStr
    reason: Literal["customer_request", "no_show", "other"]
    notes: Optional[str] = Field(None, max_length=500)

class BookingReschedule(BaseModel):
    email: EmailStr
    new_date: date
    new_time: time
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('new_date')
    def validate_new_date(cls, v):
        today = date.today()
        if v < today:
            raise ValueError("No se puede reprogramar a una fecha pasada")
        return v

class AvailabilityValidate(BaseModel):
    service_slug: str
    staff_slug: str
    date: date
    time: time

class AvailabilitySlot(BaseModel):
    start_time: time
    end_time: time
    available: bool
    reason: Optional[Literal["booked", "outside_hours", "blocked"]] = None

class DailyAvailability(BaseModel):
    date: date
    slots: list[AvailabilitySlot]

class AvailabilityResponse(BaseModel):
    business_slug: str
    service: ServiceInfo
    staff: StaffInfo
    availability: list[DailyAvailability]