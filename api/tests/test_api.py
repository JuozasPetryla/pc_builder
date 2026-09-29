from fastapi.testclient import TestClient

BUILD_PAYLOAD = {
    "name": "API testų komplektas",
    "description": "Testinis PC.",
    "is_public": False,
}
COMPONENT_PAYLOAD = {
    "category": "cpu",
    "manufacturer": "Intel",
    "model": "Core Ultra 7 Demo",
    "description": "Testinis procesorius.",
    "specifications": {"socket": "LGA1851", "cores": 20, "tdp_watts": 125},
}
OFFER_PAYLOAD = {
    "retailer": "Test Shop",
    "price": "399.99",
    "product_url": "https://example.com/cpu",
    "in_stock": True,
}
REVIEW_PAYLOAD = {"rating": 5, "comment": "Puikus komplektas."}


def test_all_crud_operations(client: TestClient) -> None:
    response = client.post("/api/v1/builds", json=BUILD_PAYLOAD)
    assert response.status_code == 201
    build = response.json()
    build_url = build["links"]["self"]
    components_url = build["links"]["components"]
    assert client.get("/api/v1/builds").status_code == 200
    assert client.get(build_url).status_code == 200
    assert (
        client.put(build_url, json={**BUILD_PAYLOAD, "is_public": True}).json()["is_public"] is True
    )

    response = client.post(components_url, json=COMPONENT_PAYLOAD)
    assert response.status_code == 201
    component = response.json()
    assert component["build_id"] == build["id"]
    component_url = component["links"]["self"]
    assert client.get(components_url).json()[0]["id"] == component["id"]
    assert client.get(component_url).status_code == 200
    response = client.put(
        component_url, json={**COMPONENT_PAYLOAD, "description": "Atnaujintas procesorius."}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Atnaujintas procesorius."

    offers_url = component["links"]["offers"]
    response = client.post(offers_url, json=OFFER_PAYLOAD)
    assert response.status_code == 201
    offer = response.json()
    assert offer["component_id"] == component["id"]
    offer_url = offer["links"]["self"]
    assert client.get(offers_url).json()[0]["id"] == offer["id"]
    assert client.get(offer_url).status_code == 200
    response = client.put(offer_url, json={**OFFER_PAYLOAD, "price": "379.99", "in_stock": False})
    assert response.status_code == 200
    assert response.json()["price"] == "379.99"
    assert response.json()["in_stock"] is False

    reviews_url = build["links"]["reviews"]
    response = client.post(reviews_url, json=REVIEW_PAYLOAD)
    assert response.status_code == 201
    review_url = response.json()["links"]["self"]
    assert len(client.get(reviews_url).json()) == 1
    assert client.get(review_url).status_code == 200
    assert client.put(review_url, json={**REVIEW_PAYLOAD, "rating": 4}).json()["rating"] == 4

    composed = client.get(build_url).json()
    assert composed["components"][0]["offers"][0]["id"] == offer["id"]
    assert composed["reviews"][0]["rating"] == 4
    for url in (review_url, offer_url, component_url, build_url):
        response = client.delete(url)
        assert response.status_code == 204
        assert response.content == b""
        assert client.get(url).status_code == 404


def test_openapi_documents_four_crud_groups(client: TestClient) -> None:
    specification = client.get("/api/openapi.json").json()
    operations = [op for methods in specification["paths"].values() for op in methods.values()]
    assert len(operations) == 30
    assert len({op["operationId"] for op in operations}) == len(operations)
    assert all(op.get("summary") and op.get("description") for op in operations)
    for tag in ("Komplektai", "Komponentai", "Atsiliepimai", "Pardavėjų pasiūlymai"):
        assert sum(tag in op["tags"] for op in operations) == 5
    assert "/api/v1/builds/{build_id}/components/{component_id}/offers" in specification["paths"]
    assert not any("categories" in path for path in specification["paths"])
