from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.eligibility.router import router as eligibility_router
from app.supabase_client import get_supabase_client

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Vector12 clinical-trial eligibility matching API.",
)

app.include_router(eligibility_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "vector12-api",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "vector12-api",
        "environment": settings.environment,
    }


@app.get("/ready")
def ready() -> dict[str, str]:
    if not settings.supabase_configured:
        raise HTTPException(
            status_code=503,
            detail="Supabase configuration is missing",
        )

    get_supabase_client()

    return {
        "status": "ready",
        "supabase": "configured",
        "compiler": (
            "configured" if settings.openai_configured else "not_configured"
        ),
    }
