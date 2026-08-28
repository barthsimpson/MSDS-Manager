import ast
from pathlib import Path

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float, Numeric

from app.domain.enums import (
    BhpDecisionStatus,
    DecisionRecordStatus,
    EvidenceFileFormat,
    EvidenceType,
    FileAvailabilityStatus,
    ProductUsageStatus,
    SafetyInformationStatus,
    SdsDocumentStatus,
)
from app.infrastructure.db.models import (
    Base,
    BhpDecisionModel,
    DecisionEvidenceModel,
    SafetyProfileModel,
    SdsDocumentModel,
)


EXPECTED_TABLES = {
    "manufacturers",
    "products",
    "usage_locations",
    "product_usage_locations",
    "sds_documents",
    "bhp_decisions",
    "decision_evidence",
    "safety_profiles",
    "sds_components",
}


def foreign_key_targets(table_name: str) -> set[str]:
    return {
        foreign_key.target_fullname
        for foreign_key in Base.metadata.tables[table_name].foreign_keys
    }


def test_metadata_contains_exactly_the_nine_core_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_every_table_has_the_expected_primary_key() -> None:
    expected = {
        "manufacturers": {"manufacturer_id"},
        "products": {"product_id"},
        "usage_locations": {"location_id"},
        "product_usage_locations": {"product_id", "location_id"},
        "sds_documents": {"sds_id"},
        "bhp_decisions": {"decision_id"},
        "decision_evidence": {"evidence_id"},
        "safety_profiles": {"sds_id"},
        "sds_components": {"component_id"},
    }

    actual = {
        table_name: {column.name for column in table.primary_key.columns}
        for table_name, table in Base.metadata.tables.items()
    }
    assert actual == expected


def test_foreign_keys_match_core_relations() -> None:
    assert foreign_key_targets("products") == {"manufacturers.manufacturer_id"}
    assert foreign_key_targets("product_usage_locations") == {
        "products.product_id",
        "usage_locations.location_id",
    }
    assert foreign_key_targets("sds_documents") == {"products.product_id"}
    assert foreign_key_targets("bhp_decisions") == {
        "products.product_id",
        "sds_documents.sds_id",
        "sds_documents.product_id",
        "decision_evidence.evidence_id",
    }
    assert foreign_key_targets("safety_profiles") == {"sds_documents.sds_id"}
    assert foreign_key_targets("sds_components") == {"sds_documents.sds_id"}


def test_product_usage_location_is_the_decimal_association_table() -> None:
    table = Base.metadata.tables["product_usage_locations"]

    assert {column.name for column in table.columns} == {
        "product_id",
        "location_id",
        "quantity_value",
        "quantity_unit",
    }
    assert isinstance(table.c.quantity_value.type, Numeric)
    assert not isinstance(table.c.quantity_value.type, Float)


def test_safety_profile_is_one_to_one_with_sds() -> None:
    table = Base.metadata.tables["safety_profiles"]

    assert table.c.sds_id.primary_key
    assert SdsDocumentModel.safety_profile.property.uselist is False
    assert SafetyProfileModel.sds_document.property.uselist is False


def test_decision_evidence_is_one_to_one_with_bhp_decision() -> None:
    evidence_id = Base.metadata.tables["bhp_decisions"].c.evidence_id

    assert evidence_id.unique
    assert BhpDecisionModel.evidence.property.uselist is False
    assert DecisionEvidenceModel.decision.property.uselist is False


def test_enum_columns_contain_only_approved_values() -> None:
    expected = {
        ("products", "usage_status"): ProductUsageStatus,
        ("sds_documents", "document_status"): SdsDocumentStatus,
        ("sds_documents", "file_status"): FileAvailabilityStatus,
        ("bhp_decisions", "decision_status"): BhpDecisionStatus,
        ("bhp_decisions", "record_status"): DecisionRecordStatus,
        ("decision_evidence", "evidence_type"): EvidenceType,
        ("decision_evidence", "file_format"): EvidenceFileFormat,
        ("decision_evidence", "file_status"): FileAvailabilityStatus,
    }
    safety_columns = {
        "hazardous_classification_status",
        "pbt_status",
        "vpvb_status",
        "carcinogenicity_status",
        "germ_cell_mutagenicity_status",
        "reproductive_toxicity_status",
        "endocrine_section_2_status",
        "endocrine_section_11_status",
        "skin_sensitization_status",
        "respiratory_sensitization_status",
    }
    expected.update(
        {("safety_profiles", column): SafetyInformationStatus for column in safety_columns}
    )

    for (table_name, column_name), enum_class in expected.items():
        column_type = Base.metadata.tables[table_name].c[column_name].type
        assert isinstance(column_type, SqlEnum)
        assert column_type.native_enum is False
        assert column_type.create_constraint is True
        assert column_type.enums == [member.value for member in enum_class]


def test_optional_columns_are_nullable() -> None:
    optional_columns = {
        "sds_documents": {"issue_date", "revision"},
        "bhp_decisions": {"notes"},
        "safety_profiles": {
            "product_definition",
            "clp_classification_text",
            "signal_word",
            "last_manual_edit_at",
        },
        "sds_components": {
            "cas_number",
            "ec_number",
            "reach_registration_number",
            "concentration_text",
            "classification_text",
        },
    }

    for table_name, column_names in optional_columns.items():
        table = Base.metadata.tables[table_name]
        assert all(table.c[column_name].nullable for column_name in column_names)


def test_required_business_columns_are_not_nullable() -> None:
    required_columns = {
        "products": {
            "product_name",
            "manufacturer_product_code",
            "manufacturer_id",
            "use_description",
            "use_restriction",
            "usage_status",
        },
        "sds_documents": {
            "product_id",
            "original_filename",
            "relative_path",
            "document_status",
            "registered_at",
            "file_status",
        },
        "bhp_decisions": {
            "product_id",
            "sds_id",
            "decision_status",
            "registered_at",
            "record_status",
            "evidence_id",
        },
    }

    for table_name, column_names in required_columns.items():
        table = Base.metadata.tables[table_name]
        assert not any(table.c[column_name].nullable for column_name in column_names)


def test_unapproved_columns_and_tables_are_absent() -> None:
    all_column_names = {
        column.name for table in Base.metadata.tables.values() for column in table.columns
    }

    assert "peak_factory_quantity" not in all_column_names
    assert "decided_by" not in all_column_names
    assert "decision_date" not in all_column_names
    assert "confidence_score" not in all_column_names
    assert not any(
        forbidden in table_name
        for table_name in Base.metadata.tables
        for forbidden in ("warehouse", "inventory", "supplier")
    )


def test_importable_model_package_contains_no_create_all_call() -> None:
    models_path = Path(__file__).resolve().parents[2] / "app" / "infrastructure" / "db" / "models"

    for source_path in models_path.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_all"
        ]
        assert calls == [], source_path


def test_relationships_do_not_cascade_deletes() -> None:
    for mapper in Base.registry.mappers:
        for relation in mapper.relationships:
            assert "delete" not in relation.cascade


def test_core_integrity_constraints_are_present_in_metadata() -> None:
    sds_table = Base.metadata.tables["sds_documents"]
    decision_table = Base.metadata.tables["bhp_decisions"]

    assert "uq_sds_documents_one_current_per_product" in {
        index.name for index in sds_table.indexes
    }
    assert "uq_bhp_decisions_one_current_per_sds" in {
        index.name for index in decision_table.indexes
    }
    assert "uq_sds_documents_sds_product" in {
        constraint.name for constraint in sds_table.constraints
    }
    assert "fk_bhp_decisions_sds_product" in {
        constraint.name for constraint in decision_table.constraints
    }
