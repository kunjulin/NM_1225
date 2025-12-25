from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrderCase(Base):
    __tablename__ = "order_cases"
    __table_args__ = (
        Index("ix_order_cases_status_updated_at", "status", "updated_at"),
        Index("ix_order_cases_patient_ref_updated_at", "patient_ref", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_ref: Mapped[str] = mapped_column(String, index=True, nullable=False)
    service_request_ref: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, nullable=False)
    owner_subject: Mapped[str | None] = mapped_column(String, nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    local_facts_json: Mapped[str] = mapped_column(Text, nullable=False)
    draft_json: Mapped[str] = mapped_column(Text, nullable=False)
    final_fhir_medication_request_ref: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class ReviewEvent(Base):
    __tablename__ = "review_events"
    __table_args__ = (
        Index("ix_review_events_case_id_created_at", "case_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("order_cases.id"), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    actor_subject: Mapped[str] = mapped_column(String, nullable=False)
    acting_role: Mapped[str] = mapped_column(String, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Outbox(Base):
    __tablename__ = "outbox"
    __table_args__ = (
        Index("ix_outbox_status_next_retry_at", "status", "next_retry_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("order_cases.id"), index=True, nullable=False
    )
    operation: Mapped[str] = mapped_column(String, nullable=False)
    request_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    next_retry_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
