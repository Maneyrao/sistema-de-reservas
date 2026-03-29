from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class StaffService(Base):
    __tablename__ = "staff_service"
    __table_args__ = (
        UniqueConstraint("staff_id", "service_id", name="uq_staff_service_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    staff = relationship("Staff", back_populates="staff_services")
    service = relationship("Service", back_populates="staff_services")
