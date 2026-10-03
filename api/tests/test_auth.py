from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import select
from test_api import BUILD_PAYLOAD, OFFER_PAYLOAD, REVIEW_PAYLOAD

from app.core.config import settings
from app.core.security import hash_refresh, password_hash
from app.models.auth import AuthSession, User
from app.models.domain import RetailOffer


def account(client, name="alice"):
    credentials = {"username": name, "password": "very-good-password"}
    response = client.post("/api/v1/auth/register", json=credentials)
    assert response.status_code == 201
    tokens = client.post("/api/v1/auth/login", json=credentials)
    assert tokens.status_code == 200
    return response.json(), tokens.json()


def use(client, tokens):
    client.headers["Authorization"] = "Bearer " + tokens["access_token"]


def test_register_login_claims_and_password_storage(anonymous_client, seeded_db):
    client = anonymous_client
    user, tokens = account(client)
    stored = seeded_db.get(User, user["id"])
    assert stored.password_hash.startswith("$argon2id$")
    assert password_hash.verify("very-good-password", stored.password_hash)
    assert user == {"id": user["id"], "username": "alice", "role": "user"}
    claims = jwt.decode(
        tokens["access_token"],
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
    assert claims["sub"] == str(user["id"]) and claims["role"] == "user"
    assert claims["exp"] - claims["iat"] == 900
    session = seeded_db.scalar(select(AuthSession))
    assert session.refresh_hash == hash_refresh(tokens["refresh_token"])
    assert session.refresh_hash != tokens["refresh_token"]
    use(client, tokens)
    assert client.get("/api/v1/auth/me").json() == user
    assert (
        client.post(
            "/api/v1/auth/register", json={"username": " ALICE ", "password": "another-password"}
        ).status_code
        == 409
    )
    for name in ["alice", "unknown"]:
        assert (
            client.post(
                "/api/v1/auth/login", json={"username": name, "password": "wrong-password"}
            ).status_code
            == 401
        )
    for extra in [{"role": "admin"}, {"id": 1}]:
        assert (
            client.post(
                "/api/v1/auth/register",
                json={"username": "mallory", "password": "valid-password", **extra},
            ).status_code
            == 422
        )


def test_rotation_logout_and_other_sessions(anonymous_client):
    client = anonymous_client
    _, first = account(client)
    second = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "very-good-password"}
    ).json()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    rotated = response.json()
    assert rotated["refresh_token"] != first["refresh_token"]
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        ).status_code
        == 401
    )
    use(client, rotated)
    assert client.post("/api/v1/auth/logout").status_code == 204
    for pair in [first, rotated]:
        use(client, pair)
        assert client.get("/api/v1/auth/me").status_code == 401
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
            ).status_code
            == 401
        )
    use(client, second)
    assert client.get("/api/v1/auth/me").status_code == 200


def test_invalid_expired_and_wrong_type_tokens(anonymous_client, seeded_db):
    client = anonymous_client
    _, tokens = account(client)
    claims = jwt.decode(tokens["access_token"], options={"verify_signature": False})
    invalid = ["garbage", tokens["refresh_token"]]
    for changes in [
        {"exp": 1},
        {"type": "refresh"},
        {"role": "admin"},
        {"aud": "wrong"},
        {"iss": "wrong"},
        {"sub": "-1"},
        {"sid": []},
    ]:
        invalid.append(
            jwt.encode(
                {**claims, **changes}, settings.jwt_secret.get_secret_value(), algorithm="HS256"
            )
        )
    invalid.append(
        jwt.encode(claims, "wrong-signature-key-at-least-32-characters", algorithm="HS256")
    )
    for token in invalid:
        client.headers["Authorization"] = f"Bearer {token}"
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    # Access expiry is recoverable while the refresh session remains valid.
    client.headers.clear()
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    session = seeded_db.scalar(select(AuthSession))
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    seeded_db.commit()
    use(client, tokens)
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refreshed.json()["refresh_token"]}
        ).status_code
        == 401
    )


def test_every_domain_endpoint_requires_login(anonymous_client):
    client = anonymous_client
    paths = client.get("/api/openapi.json").json()["paths"]
    for path, operations in paths.items():
        if "/auth/" in path:
            continue
        for method in operations:
            import re

            url = re.sub(r"\{[^}]+\}", "1", path)
            assert client.request(method, url, json={}).status_code == 401, (method, path)


@pytest.mark.parametrize("public", [False, True])
def test_ownership_and_private_hierarchy(anonymous_client, seeded_db, public):
    client = anonymous_client
    owner, tokens = account(client)
    use(client, tokens)
    build = client.post("/api/v1/builds", json={**BUILD_PAYLOAD, "is_public": public}).json()
    selection = {"catalog_component_id": 1}
    component = client.post(build["links"]["components"], json=selection).json()
    assert client.post(component["links"]["offers"], json=OFFER_PAYLOAD).status_code == 403
    stored_offer = RetailOffer(component_id=1, retailer="Private test shop", **OFFER_PAYLOAD)
    seeded_db.add(stored_offer)
    seeded_db.commit()
    offer = client.get(f"/api/v1/offers/{stored_offer.id}").json()
    review = client.post(build["links"]["reviews"], json=REVIEW_PAYLOAD).json()
    assert build["owner_id"] == review["author_id"] == owner["id"]
    _, other = account(client, "bob")
    use(client, other)
    visible = client.get("/api/v1/builds").json()
    assert (build["id"] in [b["id"] for b in visible]) == public
    for entity in [build, review]:
        for url in entity["links"].values():
            assert client.get(url).status_code == (200 if public else 404)
    for url in (
        component["links"]["self"],
        component["links"]["build"],
        component["links"]["offers"],
    ):
        assert client.get(url).status_code == (200 if public else 404)
    assert client.get(component["links"]["catalog"]).status_code == 200
    for url in offer["links"].values():
        assert client.get(url).status_code == 200
    for entity, payload in [
        (build, BUILD_PAYLOAD),
        (component, selection),
        (offer, OFFER_PAYLOAD),
        (review, REVIEW_PAYLOAD),
    ]:
        for method in ["put", "delete"]:
            assert client.request(method, entity["links"]["self"], json=payload).status_code in [
                403,
                404,
            ]
    assert client.post(build["links"]["components"], json=selection).status_code == 403
    assert client.post(component["links"]["offers"], json=OFFER_PAYLOAD).status_code == 403
    assert client.post(build["links"]["reviews"], json=REVIEW_PAYLOAD).status_code == (
        201 if public else 404
    )
    use(client, tokens)
    for entity, payload in [
        (build, {**BUILD_PAYLOAD, "is_public": public}),
        (component, selection),
        (offer, OFFER_PAYLOAD),
        (review, REVIEW_PAYLOAD),
    ]:
        expected = 403 if entity is offer else 200
        assert client.put(entity["links"]["self"], json=payload).status_code == expected
    for payload in [{"owner_id": owner["id"] + 1}, {"owner_name": "bob"}]:
        assert client.post("/api/v1/builds", json={**BUILD_PAYLOAD, **payload}).status_code == 422
    assert (
        client.post(
            build["links"]["reviews"], json={**REVIEW_PAYLOAD, "author_id": owner["id"] + 1}
        ).status_code
        == 422
    )


def test_roles_and_session_revocation(client, seeded_db):
    admin_auth = client.headers["Authorization"]
    user, tokens = account(client)
    use(client, tokens)
    review = client.post("/api/v1/builds/1/reviews", json=REVIEW_PAYLOAD).json()
    assert client.put(f"/api/v1/users/{user['id']}/role", json={"role": "admin"}).status_code == 403
    assert client.delete("/api/v1/reviews/1").status_code == 403
    client.headers["Authorization"] = admin_auth
    assert (
        client.put(f"/api/v1/users/{user['id']}/role", json={"role": "moderator"}).status_code
        == 200
    )
    use(client, tokens)
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "very-good-password"}
    ).json()
    use(client, tokens)
    assert client.put("/api/v1/reviews/1", json=REVIEW_PAYLOAD).status_code == 403
    assert client.delete("/api/v1/reviews/1").status_code == 204
    assert client.get("/api/v1/builds/2").status_code == 404
    assert client.put(f"/api/v1/users/{user['id']}/role", json={"role": "admin"}).status_code == 403
    client.headers["Authorization"] = admin_auth
    assert client.put(review["links"]["self"], json=REVIEW_PAYLOAD).status_code == 403
    assert client.delete("/api/v1/builds/2").status_code == 204


def test_legacy_names_cannot_be_claimed(anonymous_client):
    client = anonymous_client
    _, tokens = account(client, "Jonas")
    use(client, tokens)
    assert client.get("/api/v1/builds/1").json()["owner_id"] is None
    assert client.delete("/api/v1/builds/1").status_code == 403
