from datetime import date, datetime
from pydantic import BaseModel


class AvailabilityRequest(BaseModel):
    staff_id: int
    service_id: int
    date_from: date
    date_to: date


class SlotOut(BaseModel):
    start: datetime
    end: datetime
