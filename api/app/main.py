from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.web import mount_frontend

OPENAPI_TAGS = [
    {
        "name": "Komplektai",
        "description": "Kompiuterio komplekto CRUD ir visų komplektų sąrašas.",
    },
    {
        "name": "Komponentai",
        "description": "Konkrečiam komplektui priklausančių komponentų CRUD ir sąrašas.",
    },
    {
        "name": "Atsiliepimai",
        "description": (
            "Atsiliepimo CRUD ir hierarchinis konkretaus komplekto atsiliepimų sąrašas."
        ),
    },
    {
        "name": "Pardavėjų pasiūlymai",
        "description": ("Komplekto komponento pardavėjų pasiūlymų CRUD ir trijų lygių sąrašas."),
    },
]

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={"name": "Juozas Petryla"},
    openapi_tags=OPENAPI_TAGS,
)


@app.exception_handler(RequestValidationError)
async def validation_error_response(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # Echoing invalid input (e.g. NaN or a lone Unicode surrogate) would itself
    # fail JSON serialization. Keep the documented location/message/type only.
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()
            ]
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/healthz", include_in_schema=False)
def health():
    # Platform probes must not keep Neon's database compute awake.
    return {"status": "ok"}


mount_frontend(app, settings.static_dir)
