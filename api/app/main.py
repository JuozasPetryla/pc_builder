from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

OPENAPI_TAGS = [
    {
        "name": "Komponentai",
        "description": "Komponento su specifikacijomis CRUD ir katalogo sąrašas.",
    },
    {
        "name": "Komplektai",
        "description": "Kompiuterio komplekto CRUD ir visų komplektų sąrašas.",
    },
    {
        "name": "Atsiliepimai",
        "description": (
            "Atsiliepimo CRUD ir hierarchinis konkretaus komplekto atsiliepimų sąrašas."
        ),
    },
    {
        "name": "Pardavėjų pasiūlymai",
        "description": (
            "Komponento pardavėjų pasiūlymų CRUD ir konkretaus komponento pasiūlymų sąrašas."
        ),
    },
]

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "REST API kompiuterių komponentų katalogui, komplektams, "
        "suderinamumui, kainoms ir atsiliepimams."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={"name": "Juozas Petryla"},
    openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
