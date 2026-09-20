from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.presenters import review_to_read
from app.api.routes.builds import get_build_or_404
from app.db.session import get_db
from app.models.domain import Review
from app.schemas.common import ErrorResponse
from app.schemas.review import ReviewCreate, ReviewRead, ReviewReplace

router = APIRouter(tags=["Atsiliepimai"])
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Atsiliepimas nerastas."}}


def _get_review(db: Session, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Atsiliepimas nerastas.")
    return review


@router.get(
    "/builds/{build_id}/reviews",
    response_model=list[ReviewRead],
    operation_id="listBuildReviews",
    summary="Gauti komplekto atsiliepimų sąrašą",
    description=(
        "Hierarchinis sąrašo metodas: grąžina visus konkrečiam komplektui "
        "priklausančius atsiliepimus."
    ),
    responses={404: {"model": ErrorResponse, "description": "Komplektas nerastas."}},
)
def list_build_reviews(
    build_id: int,
    rating: int | None = Query(default=None, ge=1, le=5),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=2_147_483_647),
    db: Session = Depends(get_db),
) -> list[ReviewRead]:
    get_build_or_404(db, build_id)
    query = (
        select(Review)
        .where(Review.build_id == build_id)
        .order_by(Review.id)
        .offset(offset)
        .limit(limit)
    )
    if rating is not None:
        query = query.where(Review.rating == rating)
    return [review_to_read(review) for review in db.scalars(query).all()]


@router.post(
    "/builds/{build_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="createBuildReview",
    summary="Įvertinti ir pakomentuoti komplektą",
    description="Prideda 1–5 balų įvertinimą ir tekstinį komentarą prie komplekto.",
    responses={
        404: {"model": ErrorResponse, "description": "Komplektas nerastas."},
        422: {"description": "Neteisingas įvertinimas arba komentaras."},
    },
)
def create_review(
    build_id: int, payload: ReviewCreate, db: Session = Depends(get_db)
) -> ReviewRead:
    get_build_or_404(db, build_id)
    review = Review(
        build_id=build_id,
        author_name=payload.author_name,
        rating=payload.rating,
        comment=payload.comment,
        created_at=datetime.now(UTC),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review_to_read(review)


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewRead,
    operation_id="getReview",
    summary="Gauti atsiliepimą",
    description="Grąžina vieną atsiliepimą pagal jo identifikatorių.",
    responses=NOT_FOUND,
)
def get_review(review_id: int, db: Session = Depends(get_db)) -> ReviewRead:
    return review_to_read(_get_review(db, review_id))


@router.put(
    "/reviews/{review_id}",
    response_model=ReviewRead,
    operation_id="replaceReview",
    summary="Atnaujinti atsiliepimą",
    description="Pilnai pakeičia atsiliepimo autorių, įvertinimą ir komentarą.",
    responses={
        **NOT_FOUND,
        422: {"description": "Neteisingas įvertinimas arba komentaras."},
    },
)
def replace_review(
    review_id: int, payload: ReviewReplace, db: Session = Depends(get_db)
) -> ReviewRead:
    review = _get_review(db, review_id)
    review.author_name = payload.author_name
    review.rating = payload.rating
    review.comment = payload.comment
    db.commit()
    db.refresh(review)
    return review_to_read(review)


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteReview",
    summary="Pašalinti atsiliepimą",
    description="Pašalina komplekto įvertinimą ir komentarą.",
    responses=NOT_FOUND,
)
def delete_review(review_id: int, db: Session = Depends(get_db)) -> Response:
    review = _get_review(db, review_id)
    db.delete(review)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
