from sqlalchemy import Index, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from database.base import Base


class Customer(Base):
    __tablename__ = "customer"
    __table_args__ = (
        # Permite deduplicar por telefono real, pero deja convivir filas legacy con null/vacio.
        Index(
            "uq_customer_phone_not_empty",
            "phone",
            unique=True,
            sqlite_where=text("phone IS NOT NULL AND phone != ''"),
            postgresql_where=text("phone IS NOT NULL AND btrim(phone) <> ''"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    email: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    bookings = relationship("Booking", back_populates="customer")
