from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from database.base import Base


class BookingStatus(enum.Enum):
    confirmed = "confirmed"
    canceled = "canceled"


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"))
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"))

    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus))
    public_token: Mapped[str] = mapped_column(String, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    business = relationship("Business", back_populates="bookings")
    staff = relationship("Staff", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
