from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from database.base import Base


class Business(Base):
    __tablename__ = "business"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    timezone: Mapped[str] = mapped_column(String, nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hero_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hero_description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    announcement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    booking_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    maps_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    staff = relationship("Staff", back_populates="business")
    services = relationship("Service", back_populates="business")
    bookings = relationship("Booking", back_populates="business")
    admin_users = relationship("AdminUser", back_populates="business")
    time_blocks = relationship("TimeBlock", back_populates="business")
    audit_logs = relationship("AuditLog", back_populates="business")
