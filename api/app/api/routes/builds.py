from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.presenters import build_to_read
from app.db.session import get_db
from app.models.domain import Build, Component
from app.schemas.build import (
    BuildCreate,
    BuildRead,
    BuildReplace,
)
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/builds", tags=["Komplektai"])
NOT_FOUND = {"model": ErrorResponse, "description": "Komplektas nerastas."}


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
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    db: Session = Depends(get_db),
) -> list[BuildRead]:
    query = _build_query().order_by(Build.id)
    if public_only:
        query = query.where(Build.is_public.is_(True))
    builds = db.scalars(query.offset(offset).limit(limit)).all()
    return [build_to_read(build) for build in builds]


@router.post(
    "",
    response_model=BuildRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createBuild",
    summary="Sukurti kompiuterio komplektą",
    description="Sukuria komplektą; jam priklausantys komponentai kuriami per komponentų API.",
    responses={
        422: {"description": "Neteisingas užklausos turinys."},
    },
)
def create_build(payload: BuildCreate, db: Session = Depends(get_db)) -> BuildRead:
    build = Build(
        name=payload.name,
        owner_name=payload.owner_name,
        description=payload.description,
        is_public=payload.is_public,
    )
    db.add(build)
    db.commit()
    return build_to_read(get_build_or_404(db, build.id))


@router.get(
    "/{build_id}",
    response_model=BuildRead,
    operation_id="getBuild",
    summary="Gauti komplektą",
    description=(
        "Sudėtinis resursas: viename atsakyme grąžina komplektą, komponentus, "
        "jų pardavėjų pasiūlymus ir komplekto atsiliepimus."
    ),
    responses={404: NOT_FOUND},
)
def get_build(build_id: int, db: Session = Depends(get_db)) -> BuildRead:
    return build_to_read(get_build_or_404(db, build_id))


@router.put(
    "/{build_id}",
    response_model=BuildRead,
    operation_id="replaceBuild",
    summary="Atnaujinti komplektą",
    description="Pilnai pakeičia komplekto metaduomenis. Komponentai ir atsiliepimai tvarkomi atskirais metodais.",
    responses={
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
    db.commit()
    return build_to_read(get_build_or_404(db, build_id))


@router.delete(
    "/{build_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteBuild",
    summary="Pašalinti komplektą",
    description="Pašalina komplektą, jo komponentus, jų pasiūlymus ir atsiliepimus.",
    responses={404: NOT_FOUND},
)
def delete_build(build_id: int, db: Session = Depends(get_db)) -> Response:
    build = get_build_or_404(db, build_id)
    db.delete(build)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
