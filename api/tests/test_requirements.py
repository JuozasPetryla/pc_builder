"""Assessment regressions for Build -> Component -> RetailOffer ownership."""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from test_api import BUILD_PAYLOAD, COMPONENT_PAYLOAD, OFFER_PAYLOAD, REVIEW_PAYLOAD

from app.db.base import Base
from app.models.domain import Build, Component, RetailOffer


def test_schema_is_a_chain_of_one_to_many_relationships() -> None:
    assert "build_components" not in Base.metadata.tables
    assert "categories" not in Base.metadata.tables
    assert not Component.__table__.c.build_id.nullable
    assert not RetailOffer.__table__.c.component_id.nullable
    for model, relation in ((Build, "components"), (Component, "offers")):
        relationship = inspect(model).relationships[relation]
        assert relationship.direction.name == "ONETOMANY"
        assert relationship.secondary is None


def test_hypermedia_and_composed_build(client: TestClient) -> None:
    build = client.get("/api/v1/builds/1").json()
    assert len(build["components"]) == 8
    assert len(build["reviews"]) == 1
    representations = [build, *build["components"], *build["reviews"]]
    for component in build["components"]:
        assert component["build_id"] == build["id"]
        representations.extend(component["offers"])
        for offer in component["offers"]:
            assert offer["component_id"] == component["id"]
            assert offer["links"]["self"] == f"/api/v1/offers/{offer['id']}"
            assert offer["links"]["component"] == component["links"]["self"]
    for entity in representations:
        assert entity["links"]["self"].startswith("/api/v1/")
        for link in entity["links"].values():
            assert client.get(link).status_code == 200, link


LIST_PATHS = [
    "/api/v1/builds",
    "/api/v1/builds/1/components",
    "/api/v1/builds/1/components/1/offers",
    "/api/v1/builds/1/reviews",
]


def test_canonical_item_urls_and_parent_links(client: TestClient) -> None:
    component = client.get("/api/v1/components/1").json()
    offer = client.get("/api/v1/offers/1").json()
    assert component["links"]["self"] == "/api/v1/components/1"
    assert component["links"]["offers"] == "/api/v1/builds/1/components/1/offers"
    assert offer["links"]["component"] == component["links"]["self"]
    assert offer["links"]["build"] == component["links"]["build"]
    assert (
        client.put("/api/v1/offers/1", json={**OFFER_PAYLOAD, "component_id": 2}).status_code == 422
    )
    assert client.get("/api/v1/offers/1").json() == offer
    paths = client.get("/api/openapi.json").json()["paths"]
    for path, parameter in (
        ("/api/v1/components/{component_id}", "component_id"),
        ("/api/v1/offers/{offer_id}", "offer_id"),
    ):
        assert set(paths[path]) == {"get", "put", "delete"}
        for operation in paths[path].values():
            assert [p["name"] for p in operation["parameters"] if p["in"] == "path"] == [parameter]
    assert "/api/v1/builds/{build_id}/components/{component_id}" not in paths
    assert "/api/v1/builds/{build_id}/components/{component_id}/offers/{offer_id}" not in paths


@pytest.mark.parametrize("path", LIST_PATHS)
def test_pagination_and_bounds(client: TestClient, path: str) -> None:
    items = client.get(path).json()
    assert client.get(path, params={"limit": 1, "offset": 0}).json() == items[:1]
    assert client.get(path, params={"limit": 1, "offset": 1}).json() == items[1:2]
    assert client.get(path, params={"offset": 999999}).json() == []
    for params in (
        {"limit": 0},
        {"limit": 201},
        {"limit": "bad"},
        {"offset": -1},
        {"offset": 9223372036854775808},
    ):
        assert client.get(path, params=params).status_code == 422


def test_filters(client: TestClient) -> None:
    assert [b["id"] for b in client.get("/api/v1/builds?public_only=true").json()] == [1]
    assert [c["id"] for c in client.get("/api/v1/builds/1/components?category=cpu").json()] == [1]
    assert client.get("/api/v1/builds/2/components?category=gpu").json() == []
    assert client.get("/api/v1/builds/1/components?category=invalid").status_code == 422
    offers = "/api/v1/builds/1/components/1/offers"
    assert len(client.get(offers + "?in_stock=true").json()) == 1
    assert client.get(offers + "?in_stock=false").json() == []
    assert len(client.get("/api/v1/builds/1/reviews?rating=5").json()) == 1
    assert client.get("/api/v1/builds/1/reviews?rating=4").json() == []


@pytest.mark.parametrize("method", ["get", "put", "delete"])
@pytest.mark.parametrize(
    "path,payload",
    [
        ("/builds/999999", BUILD_PAYLOAD),
        ("/components/999999", COMPONENT_PAYLOAD),
        ("/offers/999999", OFFER_PAYLOAD),
        ("/reviews/999999", REVIEW_PAYLOAD),
    ],
)
def test_missing_resources_return_404(
    client: TestClient, method: str, path: str, payload: dict
) -> None:
    kwargs = {"json": payload} if method == "put" else {}
    assert client.request(method, "/api/v1" + path, **kwargs).status_code == 404


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("get", "/builds/999999/components", None),
        ("post", "/builds/999999/components", COMPONENT_PAYLOAD),
        ("get", "/builds/2/components/1/offers", None),
        ("post", "/builds/2/components/1/offers", OFFER_PAYLOAD),
        ("get", "/builds/1/components/9/offers", None),
        ("post", "/builds/1/components/9/offers", OFFER_PAYLOAD),
        ("get", "/builds/999999/reviews", None),
        ("post", "/builds/999999/reviews", REVIEW_PAYLOAD),
    ],
)
def test_lists_and_creates_enforce_parent_scope(
    client: TestClient, method: str, path: str, payload: dict | None
) -> None:
    kwargs = {"json": payload} if payload is not None else {}
    assert client.request(method, "/api/v1" + path, **kwargs).status_code == 404


def test_category_conflicts_return_409_and_rollback(client: TestClient) -> None:
    original = client.get("/api/v1/builds/1").json()
    assert client.post("/api/v1/builds/1/components", json=COMPONENT_PAYLOAD).status_code == 409
    assert client.put("/api/v1/components/2", json=COMPONENT_PAYLOAD).status_code == 409
    assert client.get("/api/v1/builds/1").json() == original


def test_offer_conflicts_return_409_and_rollback(client: TestClient) -> None:
    url = "/api/v1/builds/1/components/1/offers"
    original = client.get(url).json()[0]
    duplicate = {**OFFER_PAYLOAD, "retailer": original["retailer"]}
    assert client.post(url, json=duplicate).status_code == 409
    response = client.post(url, json=OFFER_PAYLOAD)
    assert response.status_code == 201
    second = response.json()
    assert client.put(second["links"]["self"], json=duplicate).status_code == 409
    assert client.get(second["links"]["self"]).json() == second


def test_components_are_independent_snapshots(client: TestClient) -> None:
    before = client.get("/api/v1/builds/2").json()
    response = client.put("/api/v1/components/1", json=COMPONENT_PAYLOAD)
    assert response.status_code == 200
    assert len(response.json()["offers"]) == 1  # PUT only replaces component fields.
    assert client.get("/api/v1/builds/2").json() == before
    response = client.delete("/api/v1/builds/1")
    assert response.status_code == 204 and response.content == b""
    assert client.get("/api/v1/builds/2").json() == before
    assert client.get("/api/v1/components/1").status_code == 404
    assert client.get("/api/v1/offers/1").status_code == 404
    assert client.get("/api/v1/reviews/1").status_code == 404


def test_same_model_can_be_created_for_different_builds(client: TestClient) -> None:
    first_build = client.post("/api/v1/builds", json=BUILD_PAYLOAD).json()
    second_build = client.post("/api/v1/builds", json=BUILD_PAYLOAD).json()
    first = client.post(first_build["links"]["components"], json=COMPONENT_PAYLOAD)
    second = client.post(second_build["links"]["components"], json=COMPONENT_PAYLOAD)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["build_id"] != second.json()["build_id"]
    assert (
        client.put(
            first.json()["links"]["self"],
            json={**COMPONENT_PAYLOAD, "build_id": second_build["id"]},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/builds", json={**BUILD_PAYLOAD, "component_ids": [first.json()["id"]]}
        ).status_code
        == 422
    )


def test_component_delete_cascades_only_its_offers(client: TestClient) -> None:
    response = client.delete("/api/v1/components/1")
    assert response.status_code == 204 and response.content == b""
    assert client.get("/api/v1/offers/1").status_code == 404
    assert len(client.get("/api/v1/builds/1").json()["components"]) == 7
    assert client.get("/api/v1/builds/1/components/2/offers").status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {**OFFER_PAYLOAD, "product_url": "https://example.com/" + "a" * 500},
        {**OFFER_PAYLOAD, "price": float("nan")},
        {**OFFER_PAYLOAD, "price": "NaN"},
        {**OFFER_PAYLOAD, "price": -1},
        {**OFFER_PAYLOAD, "retailer": "Bad\u0000name"},
    ],
)
def test_invalid_offer_values_return_serializable_422(client: TestClient, payload: dict) -> None:
    for method, path in (
        ("post", "/api/v1/builds/1/components/1/offers"),
        ("put", "/api/v1/offers/1"),
    ):
        response = client.request(
            method,
            path,
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
        assert response.json()["detail"]


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/builds", {**BUILD_PAYLOAD, "name": "Bad\u0000PC"}),
        ("/builds", {**BUILD_PAYLOAD, "name": "Bad\ud800PC"}),
        ("/builds/1/components", {**COMPONENT_PAYLOAD, "manufacturer": "Bad\u0000name"}),
        ("/builds/1/components", {**COMPONENT_PAYLOAD, "specifications": {"tdp": float("inf")}}),
        (
            "/builds/1/components",
            {**COMPONENT_PAYLOAD, "specifications": {"socket": "Bad\u0000value"}},
        ),
        ("/builds/1/reviews", {**REVIEW_PAYLOAD, "comment": "Bad\u0000comment"}),
        ("/builds/1/reviews", {**REVIEW_PAYLOAD, "rating": 9}),
    ],
)
def test_invalid_inputs_return_422(client: TestClient, path: str, payload: dict) -> None:
    response = client.post(
        "/api/v1" + path, content=json.dumps(payload), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["detail"]


def test_postman_covers_every_operation(client: TestClient) -> None:
    collection_path = (
        Path(__file__).resolve().parents[2] / "postman/PC_Builder_API.postman_collection.json"
    )
    collection = json.loads(collection_path.read_text())
    requests = [
        (
            item["request"]["method"].lower(),
            item["request"]["url"].split("?")[0].removeprefix("{{baseUrl}}"),
        )
        for item in collection["item"]
    ]
    for path, methods in client.get("/api/openapi.json").json()["paths"].items():
        pattern = re.sub(r"\{[^{}]+\}", "[^/]+", path)
        for method in methods:
            assert any(verb == method and re.fullmatch(pattern, url) for verb, url in requests), (
                method,
                path,
            )
