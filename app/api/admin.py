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

@router.get("/logs")
def admin_logs(
    limit: int = 100,
) -> dict:
    """Return the most recent Fotobox log entries."""

    lines = diagnostic_service.get_log_lines(
        limit=limit
    )

    return {
        "count": len(lines),
        "lines": lines,
    }

