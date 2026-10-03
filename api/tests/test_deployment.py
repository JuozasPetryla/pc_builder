from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import password_hash
from app.models.auth import User
from app.web import mount_frontend
from scripts.bootstrap_admin import bootstrap_admin


def test_frontend_keeps_api_routes_and_missing_assets_separate(tmp_path: Path):
    (tmp_path / "index.html").write_text("<html>PC Builder</html>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('PC Builder')")
    app = FastAPI()

    @app.get("/api/test")
    def api_route():
        return {"api": True}

    mount_frontend(app, tmp_path)
    with TestClient(app) as client:
        assert client.get("/").headers["content-type"].startswith("text/html")
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/api/test").json() == {"api": True}
        assert client.get("/api/missing").status_code == 404
        assert client.get("/assets/missing.js").status_code == 404
        assert client.get("/.env").status_code == 404


def test_missing_frontend_fails_at_startup(tmp_path: Path):
    with pytest.raises(RuntimeError, match="index.html"):
        mount_frontend(FastAPI(), tmp_path)


def test_health_probe_does_not_require_database():
    from app.main import app

    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert "/healthz" not in client.get("/api/openapi.json").json()["paths"]


def test_bootstrap_is_idempotent_and_does_not_reset_existing_admin(db):
    bootstrap_admin(db, "deploy-admin", "initial-test-password")
    db.commit()
    user = db.scalar(select(User).where(User.username == "deploy-admin"))
    user.is_blocked = True
    bootstrap_admin(db, "deploy-admin", "different-test-password")
    db.commit()
    assert password_hash.verify("initial-test-password", user.password_hash)
    assert user.is_blocked
    assert len(db.scalars(select(User)).all()) == 1


def test_bootstrap_never_promotes_an_existing_user(db):
    db.add(User(username="existing-user", password_hash="unused", role="user"))
    db.commit()
    with pytest.raises(ValueError, match="non-admin"):
        bootstrap_admin(db, "existing-user", "test-password")
    assert db.scalar(select(User)).role == "user"


def test_bootstrap_can_be_disabled_and_rejects_partial_or_invalid_credentials(db):
    bootstrap_admin(db, None, None)
    assert db.scalar(select(User)) is None
    with pytest.raises(ValueError, match="both"):
        bootstrap_admin(db, "deploy-admin", None)
    with pytest.raises(ValueError, match="Invalid") as error:
        bootstrap_admin(db, "deploy-admin", "short")
    assert "short" not in str(error.value)
