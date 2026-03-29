from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    Time,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database.base import Base


class AvailabilityRule(Base):
    __tablename__ = "availability_rule"
    __table_args__ = (
        UniqueConstraint(
            "staff_id",
            "weekday",
            "start_time",
            "end_time",
            name="uq_availability_rule_slot",
        ),
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_availability_weekday"),
        CheckConstraint("start_time < end_time", name="ck_availability_start_before_end"),
    )

    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=lunes ... 6=domingo
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    staff = relationship("Staff", back_populates="availability_rules")
