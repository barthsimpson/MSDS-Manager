from pathlib import Path

import pytest

from app.application.dto import AddSdsRevisionInput, SdsComponentDraft
from app.application.exceptions import SdsAcceptanceValidationError
from app.application.use_cases import AddSdsRevision


class FakeValidator:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def validate_relative(self, relative_path: str) -> Path:
        self.paths.append(relative_path)
        return Path(relative_path)


class FakeRepository:
    def __init__(self) -> None:
        self.received = None

    def accept_revision(self, data: AddSdsRevisionInput) -> str:
        self.received = data
        return "revision-id"


def test_add_sds_revision_uses_selected_product_and_skips_incomplete_components() -> None:
    repository = FakeRepository()
    validator = FakeValidator()
    data = AddSdsRevisionInput(
        product_id="existing-product",
        source_relative_path="new/revision.pdf",
        components=[
            SdsComponentDraft(component_name=None, cas_number="1-1-1"),
            SdsComponentDraft(component_name="Valid component"),
        ],
    )

    result = AddSdsRevision(repository, validator).execute(data)

    assert result == "revision-id"
    assert validator.paths == ["new/revision.pdf"]
    assert repository.received is not None
    assert repository.received.product_id == "existing-product"
    assert [item.component_name for item in repository.received.components] == [
        "Valid component"
    ]


def test_add_sds_revision_allows_empty_chemical_data() -> None:
    repository = FakeRepository()

    AddSdsRevision(repository, FakeValidator()).execute(
        AddSdsRevisionInput(
            product_id="existing-product", source_relative_path="new/revision.pdf"
        )
    )

    assert repository.received is not None
    assert repository.received.components == []


@pytest.mark.parametrize(
    "field",
    ["product_id", "source_relative_path"],
)
def test_add_sds_revision_requires_identity_and_source(field: str) -> None:
    values = {
        "product_id": "existing-product",
        "source_relative_path": "new/revision.pdf",
    }
    values[field] = ""

    with pytest.raises(SdsAcceptanceValidationError):
        AddSdsRevision(FakeRepository(), FakeValidator()).execute(
            AddSdsRevisionInput(**values)
        )
