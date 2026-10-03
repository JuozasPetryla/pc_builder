from fastapi import APIRouter

from app.api.routes import auth, builds, catalog, components, offers, reviews, users

api_router = APIRouter(
    prefix="/api/v1",
    responses={
        401: {"description": "Reikalingas galiojantis access žetonas."},
        403: {"description": "Nepakanka rolės arba įrašo nuosavybės teisių."},
    },
)
api_router.include_router(builds.router)
api_router.include_router(components.router)
api_router.include_router(reviews.router)
api_router.include_router(offers.router)

api_router.include_router(auth.router)

api_router.include_router(users.router)

api_router.include_router(catalog.router)
