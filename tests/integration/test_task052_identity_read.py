"""TASK-052 SELECT-only resolver against disposable PostgreSQL."""

import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.infrastructure.config import load_settings
from app.infrastructure.db.models import ManufacturerModel, ProductModel
from app.infrastructure.db.repositories.evidence_identity_read import SqlAlchemyEvidenceIdentityRead


@pytest.fixture(scope="module")
def isolated_database():
    operator_url = make_url(load_settings().database_url)
    if operator_url.database != "msds_manager":
        pytest.skip("TASK-052 isolation requires the configured msds_manager database")
    name = f"task052_{uuid4().hex}"
    maintenance = create_engine(operator_url, isolation_level="AUTOCOMMIT")
    isolated_url = operator_url.set(database=name)
    previous = os.environ.get("DATABASE_URL")
    engine = None
    created = False
    try:
        with maintenance.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        created = True
        os.environ["DATABASE_URL"] = isolated_url.render_as_string(hide_password=False)
        command.upgrade(Config("alembic.ini"), "head")
        engine = create_engine(isolated_url)
        yield engine
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        if engine is not None:
            engine.dispose()
        if created:
            with maintenance.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        maintenance.dispose()


def test_exact_manufacturer_and_product_cardinality_without_committed_rows(isolated_database):
    engine = isolated_database
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            session = Session(bind=connection)
            read = SqlAlchemyEvidenceIdentityRead(session)
            assert read.manufacturers_named("CX80 POLSKA") == ()
            assert read.products_named("ALUCYNK") == ()

            session.execute(insert(ManufacturerModel).values(
                manufacturer_id="m1", manufacturer_name="CX80 POLSKA",
            ))
            assert len(read.manufacturers_named("CX80 POLSKA")) == 1
            session.execute(insert(ManufacturerModel), [
                {"manufacturer_id": "m2", "manufacturer_name": "CX80 POLSKA"},
                {"manufacturer_id": "m3", "manufacturer_name": "CX80"},
                {"manufacturer_id": "m4", "manufacturer_name": "Cx80"},
            ])
            assert len(read.manufacturers_named("CX80 POLSKA")) == 2
            assert [row.name for row in read.similar_manufacturers("CX80 POLSKA")] == ["CX80", "Cx80"]

            session.execute(insert(ProductModel).values(
                product_id="p1", product_name="ALUCYNK", manufacturer_product_code=None,
                manufacturer_id="m1", use_description="", use_restriction="", usage_status="ACTIVE",
            ))
            assert len(read.products_for_manufacturer("ALUCYNK", "m1", None)) == 1
            session.execute(insert(ProductModel), [
                {"product_id": "p2", "product_name": "ALUCYNK", "manufacturer_product_code": None,
                 "manufacturer_id": "m1", "use_description": "", "use_restriction": "", "usage_status": "ACTIVE"},
                {"product_id": "p3", "product_name": "ALUCYNK", "manufacturer_product_code": "KNOWN",
                 "manufacturer_id": "m1", "use_description": "", "use_restriction": "", "usage_status": "ACTIVE"},
            ])
            assert len(read.products_for_manufacturer("ALUCYNK", "m1", "KNOWN")) == 1
            session.execute(insert(ProductModel).values(
                product_id="p4", product_name="ALUCYNK", manufacturer_product_code="KNOWN",
                manufacturer_id="m1", use_description="", use_restriction="", usage_status="ACTIVE",
            ))
            assert len(read.products_for_manufacturer("ALUCYNK", "m1", "KNOWN")) == 2
            assert len(read.products_for_manufacturer("ALUCYNK", "m1", None)) == 4
            assert read.products_for_manufacturer("ALUCYNK", "m2", "KNOWN") == ()
            assert len(read.products_named("ALUCYNK")) == 4
            session.close()
        finally:
            transaction.rollback()
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ManufacturerModel)) == 0
        assert session.scalar(select(func.count()).select_from(ProductModel)) == 0
