from sqlalchemy import ForeignKey, String, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from datetime import datetime
import enum


class BookingStatus(enum.Enum):
    confirmed = "confirmed"
    canceled = "canceled"


class Booking(Base):
    __tablename__ = "booking"
    __table_args__ = (
        UniqueConstraint("staff_id", "start_datetime"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id"), nullable=False)

    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        default=BookingStatus.confirmed,
        nullable=False
    )

    public_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
