from fastapi import APIRouter

from app.api.routes import builds, components, reviews

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(components.router)
api_router.include_router(builds.router)
api_router.include_router(reviews.router)
