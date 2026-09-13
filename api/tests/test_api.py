from fastapi.testclient import TestClient

COMPONENT_PAYLOAD = {
    "category": "cpu",
    "manufacturer": "Intel",
    "model": "Core Ultra 7 Demo",
    "description": "Testinis procesorius.",
    "specifications": {"socket": "LGA1851", "cores": 20, "tdp_watts": 125},
    "offers": [
        {
            "retailer": "Test Shop",
            "price": "399.99",
            "product_url": "https://example.com/cpu",
            "in_stock": True,
        }
    ],
}


def test_all_core_operations_and_required_status_codes(client: TestClient) -> None:
    # 1–5: components CRUD
    response = client.get("/api/v1/components")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert len(response.json()) == 9

    response = client.post("/api/v1/components", json=COMPONENT_PAYLOAD)
    assert response.status_code == 201
    component_id = response.json()["id"]

    response = client.get(f"/api/v1/components/{component_id}")
    assert response.status_code == 200

    replacement = {**COMPONENT_PAYLOAD, "description": "Atnaujintas aprašymas."}
    response = client.put(f"/api/v1/components/{component_id}", json=replacement)
    assert response.status_code == 200
    assert response.json()["description"] == "Atnaujintas aprašymas."

    # 6–10: builds CRUD
    response = client.get("/api/v1/builds")
    assert response.status_code == 200

    build_payload = {
        "name": "API testų komplektas",
        "owner_name": "Testuotojas",
        "description": "Sukurtas automatiniu testu.",
        "is_public": False,
        "component_ids": [],
    }
    response = client.post("/api/v1/builds", json=build_payload)
    assert response.status_code == 201
    build_id = response.json()["id"]

    response = client.get(f"/api/v1/builds/{build_id}")
    assert response.status_code == 200

    replacement_build = {**build_payload, "is_public": True, "component_ids": list(range(1, 9))}
    response = client.put(f"/api/v1/builds/{build_id}", json=replacement_build)
    assert response.status_code == 200
    assert len(response.json()["components"]) == 8

    # Retail offers CRUD: Component -> RetailOffer hierarchy.
    initial_offer_id = client.get(f"/api/v1/components/{component_id}").json()["offers"][0]["id"]
    response = client.get(f"/api/v1/components/{component_id}/offers")
    assert response.status_code == 200
    assert [offer["id"] for offer in response.json()] == [initial_offer_id]

    response = client.get(f"/api/v1/offers/{initial_offer_id}")
    assert response.status_code == 200
    assert response.json()["retailer"] == "Test Shop"

    response = client.put(
        f"/api/v1/offers/{initial_offer_id}",
        json={
            "retailer": "Atnaujinta parduotuvė",
            "price": "389.99",
            "product_url": "https://example.com/updated-cpu",
            "in_stock": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["in_stock"] is False

    response = client.post(
        f"/api/v1/components/{component_id}/offers",
        json={
            "retailer": "Antra parduotuvė",
            "price": "379.99",
            "product_url": "https://example.com/second-cpu",
            "in_stock": True,
        },
    )
    assert response.status_code == 201
    offer_id = response.json()["id"]

    # Reviews: list, create, read, update and delete.
    response = client.post(
        f"/api/v1/builds/{build_id}/reviews",
        json={"author_name": "API testas", "rating": 5, "comment": "Veikia puikiai."},
    )
    assert response.status_code == 201
    review_id = response.json()["id"]

    response = client.get(f"/api/v1/builds/{build_id}/reviews")
    assert response.status_code == 200
    assert [review["id"] for review in response.json()] == [review_id]

    response = client.get(f"/api/v1/reviews/{review_id}")
    assert response.status_code == 200
    assert response.json()["comment"] == "Veikia puikiai."

    response = client.put(
        f"/api/v1/reviews/{review_id}",
        json={
            "author_name": "API testas",
            "rating": 4,
            "comment": "Atnaujintas atsiliepimas.",
        },
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 4
    assert response.json()["comment"] == "Atnaujintas atsiliepimas."

    response = client.delete(f"/api/v1/reviews/{review_id}")
    assert response.status_code == 204

    response = client.delete(f"/api/v1/offers/{offer_id}")
    assert response.status_code == 204

    response = client.delete(f"/api/v1/builds/{build_id}")
    assert response.status_code == 204
    response = client.delete(f"/api/v1/components/{component_id}")
    assert response.status_code == 204

    # Explicit assessment error cases.
    assert client.get("/api/v1/components/999999").status_code == 404
    assert (
        client.post(
            "/api/v1/builds/1/reviews",
            json={"author_name": "X", "rating": 9, "comment": "no"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/builds",
            json={**build_payload, "component_ids": [1, 9]},
        ).status_code
        == 400
    )


def test_openapi_documents_four_separate_crud_groups(client: TestClient) -> None:
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    specification = response.json()
    operations = [
        operation
        for path in specification["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    assert len(operations) == 20
    assert len({operation["operationId"] for operation in operations}) == 20
    assert all(operation.get("summary") for operation in operations)
    assert all(operation.get("description") for operation in operations)
    operations_per_tag: dict[str, int] = {}
    for operation in operations:
        for tag in operation["tags"]:
            operations_per_tag[tag] = operations_per_tag.get(tag, 0) + 1
    assert operations_per_tag == {
        "Komponentai": 5,
        "Komplektai": 5,
        "Atsiliepimai": 5,
        "Pardavėjų pasiūlymai": 5,
    }
    assert [tag["name"] for tag in specification["tags"]] == list(operations_per_tag)


def test_semantic_bad_payload_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/builds",
        json={
            "name": "Blogas komplektas",
            "owner_name": "Testuotojas",
            "component_ids": [1, 9],
        },
    )
    assert response.status_code == 400


def test_structurally_bad_payload_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/builds/1/reviews",
        json={"author_name": "X", "rating": 9, "comment": "no"},
    )
    assert response.status_code == 422
