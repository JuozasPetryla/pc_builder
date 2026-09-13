from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.domain import Component, ComponentCategory, RetailOffer
from app.schemas.common import ErrorResponse
from app.schemas.component import ComponentCreate, ComponentRead, ComponentReplace

router = APIRouter(prefix="/components", tags=["Komponentai"])
ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Komponentas nerastas."},
    409: {"model": ErrorResponse, "description": "Toks komponentas jau egzistuoja."},
    422: {"description": "Neteisingas užklausos turinys arba parametrai."},
}


def _get_component(db: Session, component_id: int) -> Component:
    component = db.scalar(
        select(Component)
        .where(Component.id == component_id)
        .options(selectinload(Component.offers))
    )
    if component is None:
        raise HTTPException(status_code=404, detail="Komponentas nerastas.")
    return component


def _new_offers(payload: ComponentCreate | ComponentReplace) -> list[RetailOffer]:
    return [
        RetailOffer(
            retailer=offer.retailer,
            price=offer.price,
            product_url=str(offer.product_url),
            in_stock=offer.in_stock,
        )
        for offer in payload.offers
    ]


@router.get(
    "",
    response_model=list[ComponentRead],
    operation_id="listComponents",
    summary="Gauti komponentų katalogą",
    description="Grąžina komponentus su kainomis ir įsigijimo vietomis; galima filtruoti pagal kategoriją.",
)
def list_components(
    category: ComponentCategory | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Component]:
    query = select(Component).options(selectinload(Component.offers)).order_by(Component.id)
    if category is not None:
        query = query.where(Component.category == category.value)
    return list(db.scalars(query.offset(offset).limit(limit)).all())


@router.post(
    "",
    response_model=ComponentRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createComponent",
    summary="Sukurti komponentą",
    description="Sukuria katalogo komponentą kartu su bent viena įsigijimo vieta.",
    responses=ERROR_RESPONSES,
)
def create_component(payload: ComponentCreate, db: Session = Depends(get_db)) -> Component:
    component = Component(
        category=payload.category.value,
        manufacturer=payload.manufacturer,
        model=payload.model,
        description=payload.description,
        specifications=payload.specifications,
        offers=_new_offers(payload),
    )
    db.add(component)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Toks komponentas jau egzistuoja.") from exc
    return _get_component(db, component.id)


@router.get(
    "/{component_id}",
    response_model=ComponentRead,
    operation_id="getComponent",
    summary="Gauti komponentą",
    description="Grąžina vieną komponentą, jo techninius duomenis, kainas ir pardavėjus.",
    responses={404: ERROR_RESPONSES[404]},
)
def get_component(component_id: int, db: Session = Depends(get_db)) -> Component:
    return _get_component(db, component_id)


@router.put(
    "/{component_id}",
    response_model=ComponentRead,
    operation_id="replaceComponent",
    summary="Atnaujinti komponentą",
    description="Pilnai pakeičia komponento duomenis ir jo įsigijimo vietas.",
    responses=ERROR_RESPONSES,
)
def replace_component(
    component_id: int, payload: ComponentReplace, db: Session = Depends(get_db)
) -> Component:
    component = _get_component(db, component_id)
    component.category = payload.category.value
    component.manufacturer = payload.manufacturer
    component.model = payload.model
    component.description = payload.description
    component.specifications = payload.specifications
    component.offers.clear()
    db.flush()
    component.offers = _new_offers(payload)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Toks komponentas jau egzistuoja.") from exc
    return _get_component(db, component_id)


@router.delete(
    "/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteComponent",
    summary="Pašalinti komponentą",
    description="Pašalina komponentą, jo pasiūlymus ir susiejimus su komplektais.",
    responses={404: ERROR_RESPONSES[404]},
)
def delete_component(component_id: int, db: Session = Depends(get_db)) -> Response:
    component = _get_component(db, component_id)
    db.delete(component)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
