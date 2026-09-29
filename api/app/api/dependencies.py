from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access, is_expired, unauthorized
from app.db.session import get_db
from app.models.auth import AuthSession, Role, User
from app.models.domain import Build

bearer = HTTPBearer(auto_error=False)


def get_auth_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> AuthSession:
    if credentials is None:
        raise unauthorized()
    claims = decode_access(credentials.credentials)
    session = db.get(AuthSession, claims["sid"])
    if session is None or session.revoked or is_expired(session.expires_at):
        raise unauthorized()
    user = db.get(User, session.user_id)
    if (
        user is None
        or user.is_blocked
        or str(user.id) != claims["sub"]
        or user.role != claims["role"]
    ):
        raise unauthorized()
    return session


def get_current_user(
    session: AuthSession = Depends(get_auth_session),
    db: Session = Depends(get_db),
) -> User:
    return db.get(User, session.user_id)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(403, "Reikalinga administratoriaus rolė.")
    return user


def check_owner(owner_id: int | None, user: User) -> None:
    if owner_id != user.id:
        raise HTTPException(403, "Galite keisti tik savo įrašus.")


def check_build_read(build: Build, user: User) -> None:
    if not build.is_public and build.owner_id != user.id:
        raise HTTPException(404, "Komplektas nerastas.")


def check_content_delete(owner_id: int | None, build: Build, user: User) -> None:
    check_build_read(build, user)
    if owner_id == user.id:
        return
    if build.is_public and user.role in (Role.MODERATOR, Role.ADMIN):
        return
    raise HTTPException(403, "Galite šalinti tik savo įrašus.")
