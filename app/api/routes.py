from fastapi import APIRouter


router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a basic application health status."""

    return {
        "status": "ok",
        "service": "fotobox",
    }
