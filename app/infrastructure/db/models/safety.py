"""Persistence mappings for approved SDS safety information."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import SafetyInformationStatus

from .base import Base
from .column_types import enum_column_type


def safety_status_column(name: str):
    return mapped_column(
        enum_column_type(SafetyInformationStatus, name), nullable=False
    )


class SafetyProfileModel(Base):
    __tablename__ = "safety_profiles"

    sds_id: Mapped[str] = mapped_column(
        ForeignKey("sds_documents.sds_id"), primary_key=True
    )
    product_definition: Mapped[str | None] = mapped_column(String, nullable=True)
    hazardous_classification_status: Mapped[SafetyInformationStatus] = (
        safety_status_column("sp_hazardous_status_values")
    )
    clp_classification_text: Mapped[str | None] = mapped_column(String, nullable=True)
    signal_word: Mapped[str | None] = mapped_column(String, nullable=True)
    hazard_statements: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    supplemental_hazard_statements: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False
    )
    pbt_status: Mapped[SafetyInformationStatus] = safety_status_column(
        "sp_pbt_status_values"
    )
    vpvb_status: Mapped[SafetyInformationStatus] = safety_status_column(
        "sp_vpvb_status_values"
    )
    carcinogenicity_status: Mapped[SafetyInformationStatus] = safety_status_column(
        "sp_carcinogenicity_status_values"
    )
    germ_cell_mutagenicity_status: Mapped[SafetyInformationStatus] = (
        safety_status_column("sp_mutagenicity_status_values")
    )
    reproductive_toxicity_status: Mapped[SafetyInformationStatus] = (
        safety_status_column("sp_reproductive_status_values")
    )
    endocrine_section_2_status: Mapped[SafetyInformationStatus] = (
        safety_status_column("sp_endocrine_s2_status_values")
    )
    endocrine_section_11_status: Mapped[SafetyInformationStatus] = (
        safety_status_column("sp_endocrine_s11_status_values")
    )
    skin_sensitization_status: Mapped[SafetyInformationStatus] = (
        safety_status_column("sp_skin_sensitization_status_values")
    )
    respiratory_sensitization_status: Mapped[SafetyInformationStatus] = (
        safety_status_column("sp_respiratory_sensitization_status_values")
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_manual_edit_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    sds_document: Mapped[SdsDocumentModel] = relationship(
        back_populates="safety_profile"
    )


class SdsComponentModel(Base):
    __tablename__ = "sds_components"

    component_id: Mapped[str] = mapped_column(String, primary_key=True)
    sds_id: Mapped[str] = mapped_column(
        ForeignKey("sds_documents.sds_id"), nullable=False
    )
    component_name: Mapped[str] = mapped_column(String, nullable=False)
    cas_number: Mapped[str | None] = mapped_column(String, nullable=True)
    ec_number: Mapped[str | None] = mapped_column(String, nullable=True)
    reach_registration_number: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    concentration_text: Mapped[str | None] = mapped_column(String, nullable=True)
    classification_text: Mapped[str | None] = mapped_column(String, nullable=True)
    hazard_statements: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    sds_document: Mapped[SdsDocumentModel] = relationship(back_populates="components")


from .documents import SdsDocumentModel  # noqa: E402
