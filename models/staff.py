from sqlalchemy import String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database.base import Base


class Staff(Base):
    __tablename__ = "staff"
    __table_args__ = (
        UniqueConstraint("business_id", "slug", name="uq_staff_business_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    business = relationship("Business", back_populates="staff")
    availability_rules = relationship(
        "AvailabilityRule",
        back_populates="staff",
        cascade="all, delete-orphan",
    )
    bookings = relationship("Booking", back_populates="staff")
