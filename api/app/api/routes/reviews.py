from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.routes.builds import get_build_or_404
from app.db.session import get_db
from app.models.domain import Review
from app.schemas.common import ErrorResponse
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter(tags=["Reviews"])


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
def create_review(build_id: int, payload: ReviewCreate, db: Session = Depends(get_db)) -> Review:
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
    return review


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteReview",
    summary="Pašalinti atsiliepimą",
    description="Pašalina komplekto įvertinimą ir komentarą.",
    responses={404: {"model": ErrorResponse, "description": "Atsiliepimas nerastas."}},
)
def delete_review(review_id: int, db: Session = Depends(get_db)) -> Response:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Atsiliepimas nerastas.")
    db.delete(review)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
