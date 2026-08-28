"""Persistence mappings for SDS documents, evidence, and BHP decisions."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    SdsDocumentStatus,
)

from .base import Base
from .column_types import enum_column_type


class SdsDocumentModel(Base):
    __tablename__ = "sds_documents"
    __table_args__ = (
        UniqueConstraint(
            "sds_id", "product_id", name="uq_sds_documents_sds_product"
        ),
        Index(
            "uq_sds_documents_one_current_per_product",
            "product_id",
            unique=True,
            postgresql_where=text("document_status = 'CURRENT'"),
        ),
    )

    sds_id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    relative_path: Mapped[str] = mapped_column(String, nullable=False)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    revision: Mapped[str | None] = mapped_column(String, nullable=True)
    document_status: Mapped[SdsDocumentStatus] = mapped_column(
        enum_column_type(SdsDocumentStatus, "sds_document_status_values"),
        nullable=False,
    )
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    file_status: Mapped[FileAvailabilityStatus] = mapped_column(
        enum_column_type(FileAvailabilityStatus, "file_availability_status_values"),
        nullable=False,
    )

    product: Mapped[ProductModel] = relationship(back_populates="sds_documents")
    safety_profile: Mapped[SafetyProfileModel | None] = relationship(
        back_populates="sds_document", uselist=False
    )
    components: Mapped[list[SdsComponentModel]] = relationship(
        back_populates="sds_document"
    )
    bhp_decisions: Mapped[list[BhpDecisionModel]] = relationship(
        back_populates="sds_document", overlaps="bhp_decisions,product"
    )


class DecisionEvidenceModel(Base):
    __tablename__ = "decision_evidence"

    evidence_id: Mapped[str] = mapped_column(String, primary_key=True)
    relative_path: Mapped[str] = mapped_column(String, nullable=False)
    evidence_type: Mapped[EvidenceType] = mapped_column(
        enum_column_type(EvidenceType, "evidence_type_values"), nullable=False
    )
    file_format: Mapped[EvidenceFileFormat] = mapped_column(
        enum_column_type(EvidenceFileFormat, "evidence_file_format_values"),
        nullable=False,
    )
    file_status: Mapped[FileAvailabilityStatus] = mapped_column(
        enum_column_type(FileAvailabilityStatus, "file_availability_status_values"),
        nullable=False,
    )

    decision: Mapped[BhpDecisionModel | None] = relationship(
        back_populates="evidence", uselist=False
    )


class BhpDecisionModel(Base):
    __tablename__ = "bhp_decisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["sds_id", "product_id"],
            ["sds_documents.sds_id", "sds_documents.product_id"],
            name="fk_bhp_decisions_sds_product",
        ),
        Index(
            "uq_bhp_decisions_one_current_per_sds",
            "sds_id",
            unique=True,
            postgresql_where=text("record_status = 'CURRENT'"),
        ),
    )

    decision_id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"), nullable=False
    )
    sds_id: Mapped[str] = mapped_column(String, nullable=False)
    decision_status: Mapped[BhpDecisionStatus] = mapped_column(
        enum_column_type(BhpDecisionStatus, "bhp_decision_status_values"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    record_status: Mapped[DecisionRecordStatus] = mapped_column(
        enum_column_type(DecisionRecordStatus, "decision_record_status_values"),
        nullable=False,
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("decision_evidence.evidence_id"), nullable=False, unique=True
    )

    product: Mapped[ProductModel] = relationship(
        back_populates="bhp_decisions", overlaps="bhp_decisions,sds_document"
    )
    sds_document: Mapped[SdsDocumentModel] = relationship(
        back_populates="bhp_decisions", overlaps="bhp_decisions,product"
    )
    evidence: Mapped[DecisionEvidenceModel] = relationship(
        back_populates="decision", uselist=False
    )


from .catalog import ProductModel  # noqa: E402
from .safety import SafetyProfileModel, SdsComponentModel  # noqa: E402
