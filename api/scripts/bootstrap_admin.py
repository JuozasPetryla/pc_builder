"""Create the configured deployment administrator without taking over accounts."""

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import password_hash
from app.models.auth import Role, User
from app.schemas.auth import Credentials


def bootstrap_admin(db: Session, username: str | None, password: str | None) -> None:
    if not username and not password:
        return
    if not username or not password:
        raise ValueError("Set both BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD")
    try:
        credentials = Credentials(username=username, password=password)
    except ValidationError:
        # ValidationError includes its input; never put the password in logs.
        raise ValueError("Invalid bootstrap administrator credentials") from None

    existing = db.scalar(select(User).where(User.username == credentials.username))
    if existing:
        if existing.role != Role.ADMIN:
            raise ValueError("Bootstrap username belongs to a non-admin account; choose another")
        # Restarts must not reset the password, role, or blocked status.
        return
    db.add(
        User(
            username=credentials.username,
            password_hash=password_hash.hash(credentials.password),
            role=Role.ADMIN,
        )
    )
    db.flush()
