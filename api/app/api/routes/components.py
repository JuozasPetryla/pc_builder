from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import check_build_read, check_owner, get_current_user
from app.api.presenters import component_to_read
from app.api.routes.builds import get_build_or_404
from app.db.session import get_db
from app.models.auth import User
from app.models.domain import Component, ComponentCategory
from app.schemas.common import ErrorResponse
from app.schemas.component import ComponentCreate, ComponentRead, ComponentReplace

router = APIRouter(tags=["Komponentai"])
NOT_FOUND = {
    404: {"model": ErrorResponse, "description": "Komplektas arba jo komponentas nerastas."}
}
CONFLICT = {
    409: {"model": ErrorResponse, "description": "Komplekte jau yra šios kategorijos komponentas."}
}


def get_component_or_404(
    db: Session, component_id: int, *, build_id: int | None = None
) -> Component:
    component = db.get(Component, component_id)
    if component is None or (build_id is not None and component.build_id != build_id):
        raise HTTPException(status_code=404, detail="Komplekto komponentas nerastas.")
    return component


def _commit_component(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Komplekte jau yra šios kategorijos komponentas."
        ) from exc


@router.get(
    "/builds/{build_id}/components",
    response_model=list[ComponentRead],
    operation_id="listBuildComponents",
    summary="Gauti komplekto komponentus",
    description="Puslapiuojamas konkretaus komplekto komponentų sąrašas su kategorijos filtru.",
    responses=NOT_FOUND,
)
def list_components(
    build_id: int,
    category: ComponentCategory | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ComponentRead]:
    check_build_read(get_build_or_404(db, build_id), user)
    query = select(Component).where(Component.build_id == build_id).order_by(Component.id)
    if category is not None:
        query = query.where(Component.category == category.value)
    return [
        component_to_read(component) for component in db.scalars(query.offset(offset).limit(limit))
    ]


@router.post(
    "/builds/{build_id}/components",
    response_model=ComponentRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createBuildComponent",
    summary="Sukurti komplekto komponentą",
    description="Sukuria tik šiam komplektui priklausantį komponentą. Kategorija komplekte nesikartoja.",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_component(
    build_id: int,
    payload: ComponentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ComponentRead:
    check_owner(get_build_or_404(db, build_id).owner_id, user)
    component = Component(build_id=build_id, **payload.model_dump())
    db.add(component)
    _commit_component(db)
    return component_to_read(component)


@router.get(
    "/components/{component_id}",
    response_model=ComponentRead,
    operation_id="getComponent",
    summary="Gauti komplekto komponentą",
    description="Grąžina komponentą pagal unikalų ID. Jo komplektas nurodytas build_id ir links.build.",
    responses=NOT_FOUND,
)
def get_component(
    component_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> ComponentRead:
    component = get_component_or_404(db, component_id)
    check_build_read(component.build, user)
    return component_to_read(component)


@router.put(
    "/components/{component_id}",
    response_model=ComponentRead,
    operation_id="replaceComponent",
    summary="Atnaujinti komplekto komponentą",
    description="Pakeičia komponento duomenis, nekeisdamas jo komplekto ar pasiūlymų.",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_component(
    component_id: int,
    payload: ComponentReplace,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ComponentRead:
    component = get_component_or_404(db, component_id)
    check_owner(component.build.owner_id, user)
    for field, value in payload.model_dump().items():
        setattr(component, field, value)
    _commit_component(db)
    return component_to_read(component)


@router.delete(
    "/components/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteComponent",
    summary="Pašalinti komplekto komponentą",
    description="Pašalina šio komplekto komponentą ir jo pasiūlymus; kitų komplektų neliečia.",
    responses=NOT_FOUND,
)
def delete_component(
    component_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Response:
    component = get_component_or_404(db, component_id)
    check_owner(component.build.owner_id, user)
    db.delete(component)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
