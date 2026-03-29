from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import enum

from database.base import Base


class BookingStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    canceled = "canceled"
    completed = "completed"
    no_show = "no_show"


class Booking(Base):
    __tablename__ = "booking"
    __table_args__ = (
        CheckConstraint("end_datetime > start_datetime", name="ck_booking_end_after_start"),
        UniqueConstraint(
            "business_id",
            "idempotency_key",
            name="uq_booking_business_idempotency_key",
        ),
        Index("ix_booking_staff_status_start", "staff_id", "status", "start_datetime"),
        Index("ix_booking_reminder_lookup", "status", "reminder_sent_at", "start_datetime"),
        Index("ix_booking_business_start_datetime", "business_id", "start_datetime"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"))
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"))

    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus, name="bookingstatus"))
    public_token: Mapped[str] = mapped_column(String, unique=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    canceled_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rescheduled_from_booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("booking.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    business = relationship("Business", back_populates="bookings")
    staff = relationship("Staff", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    rescheduled_from = relationship("Booking", remote_side=[id], uselist=False)
