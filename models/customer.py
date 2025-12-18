from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from datetime import datetime


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
