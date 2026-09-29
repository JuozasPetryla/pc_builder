from sqlalchemy import select
from test_api import BUILD_PAYLOAD, REVIEW_PAYLOAD
from test_auth import account, use

from app.models.auth import AuthSession, User


def test_admin_block_unblock_revokes_all_sessions(client):
    admin_auth = client.headers["Authorization"]
    user, first = account(client)
    credentials = {"username": "alice", "password": "very-good-password"}
    second = client.post("/api/v1/auth/login", json=credentials).json()
    url = f"/api/v1/users/{user['id']}/status"
    use(client, first)
    assert client.put(url, json={"is_blocked": True}).status_code == 403
    assert client.get("/api/v1/users").status_code == 403
    client.headers["Authorization"] = admin_auth
    assert client.put(url, json={"is_blocked": True}).json()["is_blocked"] is True
    assert client.post("/api/v1/auth/login", json=credentials).status_code == 401
    for tokens in [first, second]:
        use(client, tokens)
        assert client.get("/api/v1/auth/me").status_code == 401
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
            ).status_code
            == 401
        )
    client.headers["Authorization"] = admin_auth
    assert client.put(url, json={"is_blocked": False}).status_code == 200
    assert client.post("/api/v1/auth/login", json=credentials).status_code == 200
    use(client, first)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_public_profile_and_admin_list(client):
    admin_auth = client.headers["Authorization"]
    user, tokens = account(client)
    use(client, tokens)
    profile = client.get(f"/api/v1/users/{user['id']}").json()
    assert profile == {"id": user["id"], "username": "alice"}
    assert client.get("/api/v1/users/99999").status_code == 404
    client.headers["Authorization"] = admin_auth
    users = client.get("/api/v1/users?limit=1").json()
    assert len(users) == 1
    assert set(users[0]) == {"id", "username", "role", "is_blocked"}


def test_delete_account_preserves_anonymized_content_and_invalidates_tokens(client, seeded_db):
    admin_auth = client.headers["Authorization"]
    user, tokens = account(client)
    use(client, tokens)
    build = client.post("/api/v1/builds", json={**BUILD_PAYLOAD, "is_public": True}).json()
    review = client.post("/api/v1/builds/1/reviews", json=REVIEW_PAYLOAD).json()
    url = f"/api/v1/users/{user['id']}"
    assert client.delete(url).status_code == 403
    client.headers["Authorization"] = admin_auth
    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 404
    assert seeded_db.get(User, user["id"]) is None
    assert seeded_db.scalar(select(AuthSession).where(AuthSession.user_id == user["id"])) is None
    saved = client.get(build["links"]["self"]).json()
    assert saved["owner_id"] is None
    assert saved["owner_name"] == "Pašalintas naudotojas"
    saved_review = client.get(review["links"]["self"]).json()
    assert saved_review["author_id"] is None
    assert saved_review["author_name"] == "Pašalintas naudotojas"
    use(client, tokens)
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    _, replacement = account(client)
    use(client, replacement)
    assert client.delete(build["links"]["self"]).status_code == 403


def test_admin_cannot_block_or_delete_self(client):
    me = client.get("/api/v1/auth/me").json()
    url = f"/api/v1/users/{me['id']}"
    assert client.put(url + "/status", json={"is_blocked": True}).status_code == 403
    assert client.delete(url).status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 200


def test_blocked_account_cannot_use_domain_or_change_block_status(client):
    import re

    admin_auth = client.headers["Authorization"]
    user, tokens = account(client, "blocked-user")
    paths = client.get("/api/openapi.json").json()["paths"]
    assert (
        client.put(f"/api/v1/users/{user['id']}/status", json={"is_blocked": True}).status_code
        == 200
    )
    use(client, tokens)
    for path, methods in paths.items():
        if "/auth/" in path:
            continue
        url = re.sub(r"\{[^}]+\}", str(user["id"]), path)
        for method in methods:
            assert client.request(method, url, json={}).status_code == 401, (method, path)
    client.headers["Authorization"] = admin_auth
    assert (
        client.put(f"/api/v1/users/{user['id']}/role", json={"role": "moderator"}).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "blocked-user", "password": "very-good-password"},
        ).status_code
        == 401
    )


def test_account_management_rejects_invalid_inputs(client):
    user, _ = account(client, "validation-user")
    path = f"/api/v1/users/{user['id']}"
    assert client.put(path + "/role", json={"role": "guest"}).status_code == 422
    assert (
        client.put(path + "/status", json={"is_blocked": True, "role": "admin"}).status_code == 422
    )
    assert client.put("/api/v1/users/999999/status", json={"is_blocked": True}).status_code == 404
    assert client.put("/api/v1/users/999999/role", json={"role": "user"}).status_code == 404
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"username": "injected", "password": "very-good-password", "is_blocked": False},
        ).status_code
        == 422
    )
    assert client.get("/api/v1/users?limit=0").status_code == 422
    assert client.get("/api/v1/users?offset=-1").status_code == 422
