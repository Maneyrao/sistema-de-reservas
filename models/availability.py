from sqlalchemy import Column, Integer, Time, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base


class AvailabilityRule(Base):
    __tablename__ = "availability_rule"

    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=lunes ... 6=domingo
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    staff = relationship("Staff", back_populates="availability_rules")
