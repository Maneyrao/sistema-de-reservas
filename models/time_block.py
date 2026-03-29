from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class TimeBlock(Base):
    __tablename__ = "time_block"
    __table_args__ = (
        CheckConstraint("end_datetime > start_datetime", name="ck_time_block_end_after_start"),
        Index("ix_time_block_business_range", "business_id", "start_datetime", "end_datetime"),
        Index("ix_time_block_staff_range", "staff_id", "start_datetime", "end_datetime"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("business.id"), nullable=False)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", back_populates="time_blocks")
    staff = relationship("Staff", back_populates="time_blocks")
    created_by_admin = relationship("AdminUser", back_populates="created_time_blocks")
