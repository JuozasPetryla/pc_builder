from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Component, RetailOffer
from app.schemas.common import ErrorResponse
from app.schemas.component import OfferCreate, OfferRead, OfferReplace

router = APIRouter(tags=["Pardavėjų pasiūlymai"])
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Komponentas arba pasiūlymas nerastas."}}


def _get_component(db: Session, component_id: int) -> Component:
    component = db.get(Component, component_id)
    if component is None:
        raise HTTPException(status_code=404, detail="Komponentas nerastas.")
    return component


def _get_offer(db: Session, offer_id: int) -> RetailOffer:
    offer = db.get(RetailOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Pardavėjo pasiūlymas nerastas.")
    return offer


@router.get(
    "/components/{component_id}/offers",
    response_model=list[OfferRead],
    operation_id="listComponentOffers",
    summary="Gauti komponento pardavėjų pasiūlymus",
    description=(
        "Hierarchinis sąrašo metodas: grąžina visus konkretaus komponento "
        "pardavėjų pasiūlymus."
    ),
    responses=NOT_FOUND,
)
def list_component_offers(
    component_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[RetailOffer]:
    _get_component(db, component_id)
    query = (
        select(RetailOffer)
        .where(RetailOffer.component_id == component_id)
        .order_by(RetailOffer.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(query).all())


@router.post(
    "/components/{component_id}/offers",
    response_model=OfferRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createComponentOffer",
    summary="Sukurti komponento pardavėjo pasiūlymą",
    description="Prideda konkrečiam komponentui pardavėją, kainą, nuorodą ir likutį.",
    responses={
        **NOT_FOUND,
        409: {"model": ErrorResponse, "description": "Šio pardavėjo pasiūlymas jau yra."},
    },
)
def create_component_offer(
    component_id: int, payload: OfferCreate, db: Session = Depends(get_db)
) -> RetailOffer:
    _get_component(db, component_id)
    offer = RetailOffer(
        component_id=component_id,
        retailer=payload.retailer,
        price=payload.price,
        product_url=str(payload.product_url),
        in_stock=payload.in_stock,
    )
    db.add(offer)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Šio pardavėjo pasiūlymas jau yra."
        ) from exc
    db.refresh(offer)
    return offer


@router.get(
    "/offers/{offer_id}",
    response_model=OfferRead,
    operation_id="getOffer",
    summary="Gauti pardavėjo pasiūlymą",
    description="Grąžina vieną komponento pardavėjo pasiūlymą.",
    responses=NOT_FOUND,
)
def get_offer(offer_id: int, db: Session = Depends(get_db)) -> RetailOffer:
    return _get_offer(db, offer_id)


@router.put(
    "/offers/{offer_id}",
    response_model=OfferRead,
    operation_id="replaceOffer",
    summary="Atnaujinti pardavėjo pasiūlymą",
    description="Pilnai pakeičia pardavėjo pavadinimą, kainą, nuorodą ir likutį.",
    responses={
        **NOT_FOUND,
        409: {"model": ErrorResponse, "description": "Šio pardavėjo pasiūlymas jau yra."},
    },
)
def replace_offer(
    offer_id: int, payload: OfferReplace, db: Session = Depends(get_db)
) -> RetailOffer:
    offer = _get_offer(db, offer_id)
    offer.retailer = payload.retailer
    offer.price = payload.price
    offer.product_url = str(payload.product_url)
    offer.in_stock = payload.in_stock
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Šio pardavėjo pasiūlymas jau yra."
        ) from exc
    db.refresh(offer)
    return offer


@router.delete(
    "/offers/{offer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteOffer",
    summary="Pašalinti pardavėjo pasiūlymą",
    description="Pašalina pasiūlymą, nepašalindamas paties komponento.",
    responses=NOT_FOUND,
)
def delete_offer(offer_id: int, db: Session = Depends(get_db)) -> Response:
    offer = _get_offer(db, offer_id)
    db.delete(offer)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
