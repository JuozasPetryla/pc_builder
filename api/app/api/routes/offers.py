from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import check_build_read, get_current_user, require_admin
from app.api.presenters import offer_to_read
from app.api.routes.catalog import get_catalog_or_404
from app.api.routes.components import get_component_or_404
from app.db.session import get_db
from app.models.auth import User
from app.models.domain import RetailOffer
from app.schemas.common import ErrorResponse
from app.schemas.component import OfferCreate, OfferRead, OfferReplace

router = APIRouter(tags=["Pardavėjų pasiūlymai"])
NOT_FOUND = {
    404: {"model": ErrorResponse, "description": "Resursas nurodytoje hierarchijoje nerastas."}
}
CONFLICT = {409: {"model": ErrorResponse, "description": "Šio pardavėjo pasiūlymas jau yra."}}


def _get_offer(db: Session, offer_id: int) -> RetailOffer:
    offer = db.get(RetailOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Komponento pasiūlymas nerastas.")
    return offer


def _commit_offer(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Šio pardavėjo pasiūlymas jau yra.") from exc


@router.get(
    "/builds/{build_id}/components/{component_id}/offers",
    response_model=list[OfferRead],
    operation_id="listBuildComponentOffers",
    summary="Gauti komplekto komponento pasiūlymus",
    description="Trijų lygių hierarchija: komplektas → komponentas → pasiūlymai. Tikrinama priklausomybė.",
    responses=NOT_FOUND,
)
def list_component_offers(
    build_id: int,
    component_id: int,
    in_stock: bool | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OfferRead]:
    component = get_component_or_404(db, component_id, build_id=build_id)
    check_build_read(component.build, user)
    query = (
        select(RetailOffer)
        .where(RetailOffer.component_id == component.catalog_component_id)
        .order_by(RetailOffer.id)
    )
    if in_stock is not None:
        query = query.where(RetailOffer.in_stock == in_stock)
    return [offer_to_read(offer) for offer in db.scalars(query.offset(offset).limit(limit))]


@router.post(
    "/builds/{build_id}/components/{component_id}/offers",
    response_model=OfferRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createBuildComponentOffer",
    summary="Sukurti komponento pasiūlymą",
    description="Tik admin: prideda pasiūlymą matomo komplekto komponentui.",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_offer(
    build_id: int,
    component_id: int,
    payload: OfferCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> OfferRead:
    component = get_component_or_404(db, component_id, build_id=build_id)
    check_build_read(component.build, user)
    offer = RetailOffer(
        component_id=component.catalog_component_id,
        **payload.model_dump(exclude={"product_url"}),
        product_url=str(payload.product_url),
    )
    db.add(offer)
    _commit_offer(db)
    return offer_to_read(offer)


@router.get(
    "/offers/{offer_id}",
    response_model=OfferRead,
    operation_id="getOffer",
    summary="Gauti komponento pasiūlymą",
    description="Grąžina pasiūlymą pagal unikalų ID. Bendro katalogo komponentas pasiekiamas per links.",
    responses=NOT_FOUND,
)
def get_offer(
    offer_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> OfferRead:
    offer = _get_offer(db, offer_id)
    get_catalog_or_404(db, offer.component_id, user)
    return offer_to_read(offer)


@router.put(
    "/offers/{offer_id}",
    response_model=OfferRead,
    operation_id="replaceOffer",
    summary="Atnaujinti komponento pasiūlymą",
    description="Tik admin: pakeičia bendrą pasiūlymą; nauja kaina matoma visuose jį naudojančiuose komplektuose.",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_offer(
    offer_id: int,
    payload: OfferReplace,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> OfferRead:
    offer = _get_offer(db, offer_id)
    get_catalog_or_404(db, offer.component_id, user)
    offer.retailer = payload.retailer
    offer.price = payload.price
    offer.product_url = str(payload.product_url)
    offer.in_stock = payload.in_stock
    _commit_offer(db)
    return offer_to_read(offer)


@router.delete(
    "/offers/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteOffer",
    summary="Pašalinti komponento pasiūlymą",
    description="Tik admin: pašalina bendrą pasiūlymą, nekeisdamas katalogo komponento ar komplektų.",
    responses=NOT_FOUND,
)
def delete_offer(
    offer_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)
) -> Response:
    offer = _get_offer(db, offer_id)
    get_catalog_or_404(db, offer.component_id, user)
    db.delete(offer)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/catalog/components/{component_id}/offers",
    response_model=list[OfferRead],
    summary="Gauti katalogo komponento pasiūlymus",
    description="Prisijungusiems: bendri pasiūlymai su prieinamumo filtru ir puslapiavimu.",
)
def list_catalog_offers(
    component_id: int,
    in_stock: bool | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_catalog_or_404(db, component_id, user)
    query = (
        select(RetailOffer).where(RetailOffer.component_id == component_id).order_by(RetailOffer.id)
    )
    if in_stock is not None:
        query = query.where(RetailOffer.in_stock == in_stock)
    return [offer_to_read(item) for item in db.scalars(query.offset(offset).limit(limit))]


@router.post(
    "/catalog/components/{component_id}/offers",
    response_model=OfferRead,
    status_code=201,
    summary="Sukurti bendrą pardavėjo pasiūlymą",
    description="Tik administratorius kuria katalogo komponento pasiūlymą; komplekto nereikia.",
)
def create_catalog_offer(
    component_id: int,
    payload: OfferCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    get_catalog_or_404(db, component_id, user)
    item = RetailOffer(
        component_id=component_id,
        **payload.model_dump(exclude={"product_url"}),
        product_url=str(payload.product_url),
    )
    db.add(item)
    _commit_offer(db)
    return offer_to_read(item)
