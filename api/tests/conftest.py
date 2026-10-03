import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

os.environ["JWT_SECRET"] = "test-only-secret-key-at-least-32-characters"


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import issue_tokens, password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.auth import AuthSession, User
from app.models.domain import Build, CatalogComponent, Component, RetailOffer, Review


@pytest.fixture()
def db() -> Generator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def seeded_db(db: Session) -> Session:
    db.add_all(
        [
            Build(id=1, name="Žaidimų PC", owner_name="Jonas", is_public=True),
            Build(id=2, name="Darbo PC", owner_name="Ieva", is_public=False),
        ]
    )
    db.flush()
    data = [
        ("cpu", "AMD", "Ryzen 7 7800X3D", {"socket": "AM5", "cores": 8, "tdp_watts": 120}),
        (
            "motherboard",
            "MSI",
            "MAG B650",
            {"socket": "AM5", "memory_type": "DDR5", "form_factor": "ATX"},
        ),
        ("memory", "Kingston", "FURY 32GB", {"memory_type": "DDR5", "capacity_gb": 32}),
        ("gpu", "ASUS", "RTX 4070 SUPER", {"length_mm": 267, "recommended_psu_watts": 650}),
        ("storage", "Samsung", "990 PRO 2TB", {"capacity_gb": 2000, "interface": "NVMe"}),
        ("psu", "Corsair", "RM750e", {"wattage": 750}),
        ("case", "Fractal", "North", {"supported_form_factors": ["ATX"], "max_gpu_length_mm": 355}),
        ("cooler", "Noctua", "NH-D15", {"supported_sockets": ["AM5"], "tdp_capacity_watts": 220}),
        ("cpu", "AMD", "Ryzen 7 7800X3D", {"socket": "AM5", "cores": 8, "tdp_watts": 120}),
    ]
    for index, (category, manufacturer, model, specifications) in enumerate(data, start=1):
        catalog = CatalogComponent(
            id=index,
            category=category,
            manufacturer=manufacturer,
            model=model,
            specifications=specifications,
        )
        db.add(catalog)
        db.add(
            Component(
                id=index,
                build_id=1 if index <= 8 else 2,
                catalog_component_id=index,
                category=category,
            )
        )
        db.add(
            RetailOffer(
                component_id=index,
                retailer="Demo parduotuvė",
                price=Decimal("100.00") + index,
                product_url=f"https://example.com/{index}",
                in_stock=True,
            )
        )
    db.add(
        Review(
            id=1,
            build_id=1,
            author_name="Mantas",
            rating=5,
            comment="Puikus komplektas.",
            created_at=datetime.now(UTC),
        )
    )
    db.commit()
    return db


@pytest.fixture()
def anonymous_client(seeded_db: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        with Session(bind=seeded_db.get_bind(), expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def client(anonymous_client: TestClient, seeded_db: Session) -> TestClient:
    user = User(
        username="test-admin", password_hash=password_hash.hash("test-password"), role="admin"
    )
    seeded_db.add(user)
    seeded_db.flush()
    session = AuthSession(
        id=str(uuid4()), user_id=user.id, expires_at=datetime.now(UTC) + timedelta(days=7)
    )
    # General CRUD fixtures belong to the authenticated test administrator.
    seeded_db.execute(update(Build).values(owner_id=user.id))
    seeded_db.execute(update(Review).values(author_id=user.id))
    tokens = issue_tokens(user, session)
    seeded_db.add(session)
    seeded_db.commit()
    anonymous_client.headers["Authorization"] = f"Bearer {tokens.access_token}"
    return anonymous_client
