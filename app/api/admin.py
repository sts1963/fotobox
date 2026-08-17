from fastapi import APIRouter

from app.services.container import (
    diagnostic_service,
)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
)


@router.get("/status")
def admin_status() -> dict:
    """Return the complete Fotobox diagnostic status."""

    return diagnostic_service.snapshot()

