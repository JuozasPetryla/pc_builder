from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.domain import Build, Component
from app.schemas.build import (
    BuildCreate,
    BuildRead,
    BuildReplace,
)
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/builds", tags=["Komplektai"])
NOT_FOUND = {"model": ErrorResponse, "description": "Komplektas arba komponentas nerastas."}


def _build_query():
    return select(Build).options(
        selectinload(Build.components).selectinload(Component.offers),
        selectinload(Build.reviews),
    )


def get_build_or_404(db: Session, build_id: int) -> Build:
    build = db.scalar(_build_query().where(Build.id == build_id))
    if build is None:
        raise HTTPException(status_code=404, detail="Komplektas nerastas.")
    return build


def _components_for_ids(db: Session, component_ids: list[int]) -> list[Component]:
    if not component_ids:
        return []
    components = list(
        db.scalars(
            select(Component)
            .where(Component.id.in_(component_ids))
            .options(selectinload(Component.offers))
        ).all()
    )
    found_ids = {component.id for component in components}
    missing_ids = sorted(set(component_ids) - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Komponentai nerasti: {', '.join(map(str, missing_ids))}.",
        )
    categories = [component.category for component in components]
    if len(categories) != len(set(categories)):
        raise HTTPException(
            status_code=400,
            detail="Komplekte gali būti tik vienas kiekvienos kategorijos komponentas.",
        )
    return components


def _to_read(build: Build) -> BuildRead:
    return BuildRead(
        id=build.id,
        name=build.name,
        owner_name=build.owner_name,
        description=build.description,
        is_public=build.is_public,
        components=build.components,
        reviews=build.reviews,
        created_at=build.created_at,
        updated_at=build.updated_at,
    )


@router.get(
    "",
    response_model=list[BuildRead],
    operation_id="listBuilds",
    summary="Gauti komplektų sąrašą",
    description="Grąžina komplektus su komponentais, jų pardavėjų pasiūlymais ir atsiliepimais.",
)
def list_builds(
    public_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[BuildRead]:
    query = _build_query().order_by(Build.id)
    if public_only:
        query = query.where(Build.is_public.is_(True))
    builds = db.scalars(query.offset(offset).limit(limit)).all()
    return [_to_read(build) for build in builds]


@router.post(
    "",
    response_model=BuildRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createBuild",
    summary="Sukurti kompiuterio komplektą",
    description="Sukuria privatų arba viešą komplektą ir pasirinktinai iš karto priskiria komponentus.",
    responses={
        400: {"model": ErrorResponse, "description": "Komplekte kartojasi komponento kategorija."},
        404: NOT_FOUND,
        422: {"description": "Neteisingas užklausos turinys."},
    },
)
def create_build(payload: BuildCreate, db: Session = Depends(get_db)) -> BuildRead:
    components = _components_for_ids(db, payload.component_ids)
    build = Build(
        name=payload.name,
        owner_name=payload.owner_name,
        description=payload.description,
        is_public=payload.is_public,
        components=components,
    )
    db.add(build)
    db.commit()
    return _to_read(get_build_or_404(db, build.id))


@router.get(
    "/{build_id}",
    response_model=BuildRead,
    operation_id="getBuild",
    summary="Gauti komplektą",
    description=(
        "Hierarchiniu atsakymu grąžina Komplektas → komponentas → pardavėjo pasiūlymas "
        "struktūrą ir atsiliepimus."
    ),
    responses={404: NOT_FOUND},
)
def get_build(build_id: int, db: Session = Depends(get_db)) -> BuildRead:
    return _to_read(get_build_or_404(db, build_id))


@router.put(
    "/{build_id}",
    response_model=BuildRead,
    operation_id="replaceBuild",
    summary="Atnaujinti komplektą",
    description="Pilnai pakeičia komplekto metaduomenis, viešumo būseną ir komponentų sąrašą.",
    responses={
        400: {"model": ErrorResponse},
        404: NOT_FOUND,
        422: {"description": "Neteisingas turinys."},
    },
)
def replace_build(build_id: int, payload: BuildReplace, db: Session = Depends(get_db)) -> BuildRead:
    build = get_build_or_404(db, build_id)
    build.name = payload.name
    build.owner_name = payload.owner_name
    build.description = payload.description
    build.is_public = payload.is_public
    build.components = _components_for_ids(db, payload.component_ids)
    db.commit()
    return _to_read(get_build_or_404(db, build_id))


@router.delete(
    "/{build_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteBuild",
    summary="Pašalinti komplektą",
    description="Pašalina komplektą, jo komponentų susiejimus ir atsiliepimus.",
    responses={404: NOT_FOUND},
)
def delete_build(build_id: int, db: Session = Depends(get_db)) -> Response:
    build = get_build_or_404(db, build_id)
    db.delete(build)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
