from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import check_build_read, get_current_user, require_admin
from app.api.presenters import catalog_to_read
from app.api.routes.builds import get_build_or_404
from app.db.session import get_db
from app.models.auth import User
from app.models.domain import CatalogComponent, Component, ComponentCategory
from app.schemas.component import CatalogComponentRead, ComponentCreate, ComponentReplace

router = APIRouter(prefix="/catalog/components", tags=["Katalogas"])


def get_catalog_or_404(db: Session, component_id: int, user: User) -> CatalogComponent:
    component = db.get(CatalogComponent, component_id)
    if component is None:
        raise HTTPException(404, "Katalogo komponentas nerastas.")
    if component.legacy_build_id is not None:
        check_build_read(get_build_or_404(db, component.legacy_build_id), user)
    return component


def commit_catalog(db: Session):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            409, "Komponentas naudojamas komplekte; jo pašalinti arba keisti kategorijos negalima."
        ) from exc


@router.get(
    "",
    response_model=list[CatalogComponentRead],
    summary="Gauti komponentų katalogą",
    description="Visiems prisijungusiems: bendras katalogas su paieška, kategorijos filtru ir puslapiavimu.",
)
def list_catalog(
    category: ComponentCategory | None = None,
    q: str = Query(default="", max_length=120),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(CatalogComponent)
        .where(CatalogComponent.legacy_build_id.is_(None))
        .order_by(CatalogComponent.id)
    )
    if category:
        query = query.where(CatalogComponent.category == category.value)
    if q.strip():
        query = query.where(
            (CatalogComponent.manufacturer + " " + CatalogComponent.model).icontains(
                q.strip(), autoescape=True
            )
        )
    return [catalog_to_read(item) for item in db.scalars(query.offset(offset).limit(limit))]


@router.post(
    "",
    response_model=CatalogComponentRead,
    status_code=201,
    summary="Sukurti katalogo komponentą",
    description="Tik administratorius sukuria bendro katalogo komponentą; komplekto kurti nereikia.",
)
def create_catalog(
    payload: ComponentCreate, db: Session = Depends(get_db), user: User = Depends(require_admin)
):
    item = CatalogComponent(**payload.model_dump())
    db.add(item)
    commit_catalog(db)
    return catalog_to_read(item)


@router.get(
    "/{component_id}",
    response_model=CatalogComponentRead,
    summary="Gauti katalogo komponentą",
    description="Prisijungusiems grąžina bendras specifikacijas ir pasiūlymus. Seni privatūs duomenys išlaiko savo prieigos ribas.",
)
def get_catalog(
    component_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return catalog_to_read(get_catalog_or_404(db, component_id, user))


@router.put(
    "/{component_id}",
    response_model=CatalogComponentRead,
    summary="Atnaujinti katalogo komponentą",
    description="Tik administratorius; pakeitimai matomi visuose komplektuose. Naudojamo komponento kategorija nekeičiama.",
)
def replace_catalog(
    component_id: int,
    payload: ComponentReplace,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    item = get_catalog_or_404(db, component_id, user)
    if payload.category != item.category and db.scalar(
        select(Component.id).where(Component.catalog_component_id == component_id).limit(1)
    ):
        raise HTTPException(409, "Naudojamo komponento kategorijos keisti negalima.")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    commit_catalog(db)
    return catalog_to_read(item)


@router.delete(
    "/{component_id}",
    status_code=204,
    summary="Pašalinti katalogo komponentą",
    description="Tik administratorius; jei komponentas pasirinktas komplekte, grąžina 409. Nenaudojamas komponentas šalinamas su pasiūlymais.",
)
def delete_catalog(
    component_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)
):
    item = get_catalog_or_404(db, component_id, user)
    if db.scalar(
        select(Component.id).where(Component.catalog_component_id == component_id).limit(1)
    ):
        raise HTTPException(
            409, "Komponentas naudojamas komplekte. Pirmiausia pašalinkite pasirinkimus."
        )
    db.delete(item)
    commit_catalog(db)
    return Response(status_code=204)
