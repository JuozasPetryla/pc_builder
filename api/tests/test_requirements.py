"""Regressions for the shared component catalog and its access rules."""

from fastapi.testclient import TestClient
from sqlalchemy import inspect
from test_api import BUILD_PAYLOAD, COMPONENT_PAYLOAD

from app.db.base import Base
from app.models.domain import Build, CatalogComponent, Component, RetailOffer


def test_build_selection_references_shared_catalog(seeded_db) -> None:
    assert "catalog_components" in Base.metadata.tables
    assert "build_components" not in Base.metadata.tables
    assert not Component.__table__.c.build_id.nullable
    assert not RetailOffer.__table__.c.component_id.nullable
    assert inspect(Build).relationships["components"].direction.name == "ONETOMANY"
    assert inspect(CatalogComponent).relationships["offers"].direction.name == "ONETOMANY"
    assert seeded_db.get(Component, 1).catalog_component_id == 1
    assert seeded_db.get(RetailOffer, 1).component_id == 1


def test_admin_catalog_edits_are_shared_by_builds(client: TestClient) -> None:
    catalog = client.post("/api/v1/catalog/components", json=COMPONENT_PAYLOAD)
    assert catalog.status_code == 201
    catalog = catalog.json()

    builds = [client.post("/api/v1/builds", json=BUILD_PAYLOAD).json() for _ in range(2)]
    selection = {"catalog_component_id": catalog["id"]}
    selected = [client.post(build["links"]["components"], json=selection) for build in builds]
    assert all(response.status_code == 201 for response in selected)

    edited = {**COMPONENT_PAYLOAD, "model": "Shared model update", "description": "Updated once"}
    response = client.put(catalog["links"]["self"], json=edited)
    assert response.status_code == 200
    for build in builds:
        component = client.get(build["links"]["self"]).json()["components"][0]
        assert component["catalog_component_id"] == catalog["id"]
        assert component["model"] == "Shared model update"
        assert component["description"] == "Updated once"

    assert client.delete(catalog["links"]["self"]).status_code == 409


def test_regular_users_select_existing_parts_but_cannot_create_catalog_rows(
    client, anonymous_client
):
    catalog = client.get("/api/v1/catalog/components/1").json()
    assert client.post("/api/v1/catalog/components", json=COMPONENT_PAYLOAD).status_code == 403

    credentials = {"username": "catalog-user", "password": "very-good-password"}
    assert anonymous_client.post("/api/v1/auth/register", json=credentials).status_code == 201
    tokens = anonymous_client.post("/api/v1/auth/login", json=credentials).json()
    anonymous_client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    build = anonymous_client.post("/api/v1/builds", json=BUILD_PAYLOAD).json()
    response = anonymous_client.post(
        build["links"]["components"], json={"catalog_component_id": catalog["id"]}
    )
    assert response.status_code == 201
    assert response.json()["manufacturer"] == catalog["manufacturer"]
    assert (
        anonymous_client.post(build["links"]["components"], json=COMPONENT_PAYLOAD).status_code
        == 422
    )


def test_private_legacy_catalog_rows_stay_out_of_public_catalog(client):
    assert 9 not in [item["id"] for item in client.get("/api/v1/catalog/components").json()]
    assert client.get("/api/v1/catalog/components/9").status_code == 200
