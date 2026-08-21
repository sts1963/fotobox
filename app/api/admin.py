from __future__ import annotations

import logging
import subprocess

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from pydantic import BaseModel

from app.services.container import (
    background_library_service,
    diagnostic_service,
    logo_library_service,
    photo_session_service,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
)


class BackgroundSelection(BaseModel):
    filename: str


class LogoSelection(BaseModel):
    filename: str


class BackgroundModeUpdate(BaseModel):
    enabled: bool


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

@router.delete(
    "/logos/{filename}"
)
def delete_logo(
    filename: str,
) -> dict[str, str]:
    """Delete one unused logo."""

    try:
        logo_library_service.delete_logo(
            filename
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "deleted",
        "filename": filename,
    }

def _poweroff_system() -> None:
    """Power off the Raspberry Pi."""

    logger.warning(
        "System shutdown initiated"
    )

    result = subprocess.run(
        [
            "sudo",
            "-n",
            "/usr/bin/systemctl",
            "poweroff",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(
            "System shutdown failed: %s",
            result.stderr.strip(),
        )


@router.post(
    "/shutdown",
    status_code=202,
)
async def admin_shutdown(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Request a shutdown from the local service console."""

    client_host = (
        request.client.host
        if request.client is not None
        else None
    )

    if client_host not in {
        "127.0.0.1",
        "::1",
    }:
        logger.warning(
            "Rejected remote shutdown request from %s",
            client_host,
        )

        raise HTTPException(
            status_code=403,
            detail="Shutdown is only allowed locally.",
        )

    logger.warning(
        "Shutdown requested from local console"
    )

    background_tasks.add_task(
        _poweroff_system
    )

    return {
        "status": "accepted",
        "message": "System shutdown requested.",
    }


@router.get(
    "/backgrounds"
)
def admin_backgrounds() -> dict:
    """Return available virtual backgrounds."""

    return {
        "items": (
            background_library_service
            .list_backgrounds()
        ),
    }

@router.delete(
    "/backgrounds/{filename}"
)
def delete_background(
    filename: str,
) -> dict[str, str]:
    """Delete one unused background."""

    try:
        background_library_service.delete_background(
            filename
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "deleted",
        "filename": filename,
    }

@router.post(
    "/backgrounds/upload"
)
async def upload_background(
    file: UploadFile = File(...),
) -> dict[str, str]:
    """Upload one virtual background."""

    data = await file.read(
        background_library_service
        .MAX_UPLOAD_BYTES
        + 1
    )

    try:
        filename = (
            background_library_service
            .save_upload(
                file.filename
                or "background.jpg",
                data,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "filename": filename,
    }


@router.post(
    "/backgrounds/select/{slot}"
)
def select_background(
    slot: int,
    selection: BackgroundSelection,
) -> dict[str, str]:
    """Assign one background to a photo slot."""

    try:
        path = (
            background_library_service
            .select_background(
                slot=slot,
                filename=selection.filename,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "slot": str(slot),
        "filename": selection.filename,
        "active_path": str(path),
    }


@router.get(
    "/backgrounds/settings"
)
def background_settings() -> dict[str, bool]:
    """Return current virtual background state."""

    return {
        "enabled": (
            photo_session_service
            .backgrounds_enabled
        ),
    }


@router.post(
    "/backgrounds/settings"
)
def update_background_settings(
    update: BackgroundModeUpdate,
) -> dict[str, bool]:
    """Enable or disable virtual backgrounds."""

    photo_session_service.set_backgrounds_enabled(
        update.enabled
    )

    return {
        "enabled": (
            photo_session_service
            .backgrounds_enabled
        ),
    }


@router.get(
    "/logos"
)
def admin_logos() -> dict:
    """Return available and active logo state."""

    return {
        "items": (
            logo_library_service
            .list_logos()
        ),
        "active": (
            logo_library_service
            .active_logo_exists()
        ),
    }


@router.post(
    "/logos/upload"
)
async def upload_logo(
    file: UploadFile = File(...),
) -> dict[str, str]:
    """Upload one logo."""

    data = await file.read(
        logo_library_service
        .MAX_UPLOAD_BYTES
        + 1
    )

    try:
        filename = (
            logo_library_service
            .save_upload(
                file.filename
                or "logo.png",
                data,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "filename": filename,
    }


@router.post(
    "/logos/select"
)
def select_logo(
    selection: LogoSelection,
) -> dict[str, str]:
    """Activate one logo."""

    try:
        path = (
            logo_library_service
            .select_logo(
                filename=selection.filename,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "filename": selection.filename,
        "active_path": str(path),
    }
