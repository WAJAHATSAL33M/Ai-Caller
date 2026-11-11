from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200))
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    consent_status: Mapped[str] = mapped_column(String(24), default="unverified")
    consent_source: Mapped[str | None] = mapped_column(String(300), nullable=True)
    do_not_call: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(40), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    calls: Mapped[list["Call"]] = relationship(back_populates="lead")

class Call(Base):
    __tablename__ = "calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    provider_session_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="requested")
    outcome: Mapped[str] = mapped_column(String(80), default="pending")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    lead: Mapped[Lead] = relationship(back_populates="calls")
