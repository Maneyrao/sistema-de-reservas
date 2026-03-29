from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdminCreateTimeBlockRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    staff_slug: str | None = Field(default=None, description="Opcional. Si se omite es bloqueo global.")
    start_datetime: datetime
    end_datetime: datetime
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_time_range(self) -> "AdminCreateTimeBlockRequest":
        if self.end_datetime <= self.start_datetime:
            raise ValueError("end_datetime must be after start_datetime")
        return self


class AdminTimeBlockOut(BaseModel):
    id: int
    staff_id: int | None
    staff_slug: str | None
    start_datetime: str
    end_datetime: str
    reason: str | None
    notes: str | None
    created_by_admin_id: int | None
    created_at: str
