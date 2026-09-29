from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.auth import AuthSession, User
from app.models.domain import Build, Review
from app.schemas.auth import UserAdminRead, UserPublic, UserStatusUpdate

router = APIRouter(prefix="/users", tags=["Naudotojai"])


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "Naudotojas nerastas.")
    return user


def check_other_user(user_id: int, admin: User) -> None:
    if user_id == admin.id:
        raise HTTPException(403, "Negalite blokuoti arba pašalinti savo paskyros.")


@router.get("", response_model=list[UserAdminRead], summary="Gauti naudotojų sąrašą")
def list_users(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Tik administratorius gali skaityti puslapiuojamą paskyrų sąrašą ir blokavimo būsenas."""
    return db.scalars(select(User).order_by(User.id).offset(offset).limit(limit)).all()


@router.get("/{user_id}", response_model=UserPublic, summary="Gauti viešą naudotojo informaciją")
def get_public_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Prisijungusiems grąžina tik naudotojo ID ir viešą vardą."""
    return get_user(db, user_id)


@router.put(
    "/{user_id}/status", response_model=UserAdminRead, summary="Blokuoti arba atblokuoti naudotoją"
)
def change_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Tik administratorius; blokuojant atšaukiamos visos paskyros sesijos."""
    check_other_user(user_id, admin)
    user = get_user(db, user_id)
    user.is_blocked = payload.is_blocked
    if user.is_blocked:
        db.execute(update(AuthSession).where(AuthSession.user_id == user.id).values(revoked=True))
    db.commit()
    return user


@router.delete("/{user_id}", status_code=204, summary="Pašalinti naudotoją")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Tik administratorius; pašalina paskyrą ir sesijas, išsaugo anonimizuotą turinį."""
    check_other_user(user_id, admin)
    user = get_user(db, user_id)
    # Preserve shared content without leaving a reference to a deleted account.
    db.execute(
        update(Build)
        .where(Build.owner_id == user.id)
        .values(owner_id=None, owner_name="Pašalintas naudotojas")
    )
    db.execute(
        update(Review)
        .where(Review.author_id == user.id)
        .values(author_id=None, author_name="Pašalintas naudotojas")
    )
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    db.delete(user)
    db.commit()
    return Response(status_code=204)
