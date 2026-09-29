from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_auth_session, get_current_user, require_admin
from app.core.config import settings
from app.core.security import (
    DUMMY_HASH,
    hash_refresh,
    is_expired,
    issue_tokens,
    password_hash,
    unauthorized,
)
from app.db.session import get_db
from app.models.auth import AuthSession, Role, User
from app.schemas.auth import Credentials, RefreshInput, RoleUpdate, TokenPair, UserRead

router = APIRouter(tags=["Autentifikacija"])


def token_response(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post(
    "/auth/register",
    response_model=UserRead,
    status_code=201,
    summary="Registruotis",
    description="Sukuria naudotoją su user role.",
)
def register(payload: Credentials, db: Session = Depends(get_db)):
    user = User(
        username=payload.username,
        password_hash=password_hash.hash(payload.password),
        role=Role.USER,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Naudotojo vardas jau užimtas.") from exc
    return user


@router.post(
    "/auth/login",
    response_model=TokenPair,
    summary="Prisijungti",
    description="Grąžina trumpalaikį JWT ir ilgalaikį atnaujinimo žetoną.",
)
def login(payload: Credentials, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    valid = password_hash.verify(payload.password, user.password_hash if user else DUMMY_HASH)
    if not valid or user is None or user.is_blocked:
        raise HTTPException(
            401,
            "Neteisingas naudotojo vardas arba slaptažodis.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session = AuthSession(
        id=str(uuid4()),
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    tokens = issue_tokens(user, session)
    db.add(session)
    db.commit()
    token_response(response)
    return tokens


@router.post(
    "/auth/refresh",
    response_model=TokenPair,
    summary="Atnaujinti žetonus",
    description="Vieną kartą panaudoja refresh žetoną ir grąžina naują porą. Sesija galioja 7 dienas nuo prisijungimo.",
)
def refresh(payload: RefreshInput, response: Response, db: Session = Depends(get_db)):
    old_hash = hash_refresh(payload.refresh_token)
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_hash == old_hash))
    if session is None or session.revoked or is_expired(session.expires_at):
        raise unauthorized()
    user = db.get(User, session.user_id)
    if user is None or user.is_blocked:
        raise unauthorized()
    tokens = issue_tokens(user, session)
    new_hash = session.refresh_hash
    # Conditional UPDATE makes rotation single-use even for concurrent requests.
    db.expire(session, ["refresh_hash"])
    result = db.execute(
        update(AuthSession)
        .where(
            AuthSession.id == session.id,
            AuthSession.refresh_hash == old_hash,
            AuthSession.revoked.is_(False),
            AuthSession.expires_at > datetime.now(UTC),
        )
        .values(refresh_hash=new_hash)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise unauthorized()
    db.commit()
    token_response(response)
    return tokens


@router.post(
    "/auth/logout",
    status_code=204,
    summary="Atsijungti",
    description="Panaikina šios sesijos access ir refresh žetonų galiojimą.",
)
def logout(session: AuthSession = Depends(get_auth_session), db: Session = Depends(get_db)):
    session.revoked = True
    db.commit()
    return Response(status_code=204)


@router.get(
    "/auth/me",
    response_model=UserRead,
    summary="Mano paskyra",
    description="Grąžina prisijungusio naudotojo ID, vardą ir rolę.",
)
def me(user: User = Depends(get_current_user)):
    return user


@router.put(
    "/users/{user_id}/role",
    response_model=UserRead,
    summary="Pakeisti naudotojo rolę",
    description="Tik administratorius gali skirti roles. Panaikina pakeistos paskyros sesijas.",
)
def change_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(403, "Negalite keisti savo rolės.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Naudotojas nerastas.")
    user.role = payload.role
    db.execute(update(AuthSession).where(AuthSession.user_id == user.id).values(revoked=True))
    db.commit()
    return user
