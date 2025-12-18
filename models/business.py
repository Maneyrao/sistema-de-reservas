from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from datetime import datetime


class Business(Base):
    __tablename__ = "business"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    #el slug lo que hace, es darle un valor único a cada negocio. Por ejemplo, en este caso
    #se habla que es amsterdam el negocio para el que hacemos el sistema de reservas.   
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
