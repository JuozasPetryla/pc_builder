import pytest
from test_api import BUILD_PAYLOAD, COMPONENT_PAYLOAD, OFFER_PAYLOAD, REVIEW_PAYLOAD
from test_auth import account, use


@pytest.mark.parametrize("role", ["user", "moderator", "admin"])
def test_role_and_owner_matrix(client, role):
    admin_auth = client.headers["Authorization"]
    owner, owner_tokens = account(client, "owner")
    use(client, owner_tokens)
    public = client.post("/api/v1/builds", json={**BUILD_PAYLOAD, "is_public": True}).json()
    private = client.post("/api/v1/builds", json=BUILD_PAYLOAD).json()
    pub_component = client.post(public["links"]["components"], json=COMPONENT_PAYLOAD).json()
    priv_component = client.post(private["links"]["components"], json=COMPONENT_PAYLOAD).json()
    pub_review = client.post(public["links"]["reviews"], json=REVIEW_PAYLOAD).json()
    priv_review = client.post(private["links"]["reviews"], json=REVIEW_PAYLOAD).json()
    actor, _ = account(client, "actor")
    client.headers["Authorization"] = admin_auth
    assert client.put(f"/api/v1/users/{actor['id']}/role", json={"role": role}).status_code == 200
    tokens = client.post(
        "/api/v1/auth/login", json={"username": "actor", "password": "very-good-password"}
    ).json()
    use(client, tokens)
    visible = [b["id"] for b in client.get("/api/v1/builds").json()]
    assert public["id"] in visible and private["id"] not in visible
    for entity in [private, priv_component, priv_review]:
        for link in entity["links"].values():
            assert client.get(link).status_code == 404
        assert client.delete(entity["links"]["self"]).status_code in (403, 404)
    for entity, payload in [
        (public, BUILD_PAYLOAD),
        (pub_component, COMPONENT_PAYLOAD),
        (pub_review, REVIEW_PAYLOAD),
    ]:
        assert client.put(entity["links"]["self"], json=payload).status_code == 403
    assert client.delete(pub_component["links"]["self"]).status_code == 403
    offer = client.post(pub_component["links"]["offers"], json=OFFER_PAYLOAD)
    assert offer.status_code == (201 if role == "admin" else 403)
    if role == "admin":
        url = offer.json()["links"]["self"]
        assert client.put(url, json=OFFER_PAYLOAD).status_code == 200
        assert client.delete(url).status_code == 204
        assert client.post(priv_component["links"]["offers"], json=OFFER_PAYLOAD).status_code == 404
    if role != "admin":
        for method, path, payload in [
            ("get", "/users", None),
            ("put", f"/users/{owner['id']}/status", {"is_blocked": True}),
            ("put", f"/users/{owner['id']}/role", {"role": "admin"}),
            ("delete", f"/users/{owner['id']}", None),
            ("put", "/offers/1", OFFER_PAYLOAD),
            ("delete", "/offers/1", None),
        ]:
            assert client.request(method, "/api/v1" + path, json=payload).status_code == 403
    own = client.post("/api/v1/builds", json=BUILD_PAYLOAD).json()
    assert client.put(own["links"]["self"], json=BUILD_PAYLOAD).status_code == 200
    assert client.delete(own["links"]["self"]).status_code == 204
    own_review = client.post(public["links"]["reviews"], json=REVIEW_PAYLOAD).json()
    assert client.put(own_review["links"]["self"], json=REVIEW_PAYLOAD).status_code == 200
    assert client.delete(own_review["links"]["self"]).status_code == 204
    expected = 403 if role == "user" else 204
    assert client.delete(pub_review["links"]["self"]).status_code == expected
    assert client.delete(public["links"]["self"]).status_code == expected
