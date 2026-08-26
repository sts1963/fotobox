from __future__ import annotations

import logging
import subprocess

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel

from app.services.container import (
    background_library_service,
    diagnostic_service,
    logo_library_service,
    photo_session_service,
    settings_admin_service,
    greenscreen_calibration_service,
    print_service,
    test_print_service,
    session_archive_service,
    settings,
)

import io
from datetime import datetime

from fastapi.responses import (
    FileResponse,
    StreamingResponse,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
)


class BackgroundSelection(BaseModel):
    filename: str


class BackgroundRotation(BaseModel):
    degrees: int


class LogoSelection(BaseModel):
    filename: str


class BackgroundModeUpdate(BaseModel):
    enabled: bool
    selection_mode: str

class GreenscreenSettingsUpdate(
    BaseModel
):
    hue_min: int
    hue_max: int
    saturation_min: int
    value_min: int
    feather: int


class SessionSettingsUpdate(
    BaseModel
):
    countdown_seconds: int
    interval_seconds: float


class BackgroundSettingsUpdate(
    BaseModel
):
    enabled: bool
    greenscreen: GreenscreenSettingsUpdate


class FotoboxSettingsUpdate(
    BaseModel
):
    session: SessionSettingsUpdate
    background: BackgroundSettingsUpdate

class ShutdownRequest(BaseModel):
    pin: str

class GreenscreenMaskRequest(
    BaseModel
):
    hue_min: int
    hue_max: int
    saturation_min: int
    value_min: int
    use_test_image: bool = False

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

@router.get(
    "/sessions"
)
def admin_sessions() -> dict:
    """Return stored photo sessions and summary."""

    sessions = (
        session_archive_service
        .list_sessions()
    )

    return {
        "summary": (
            session_archive_service
            .get_summary()
        ),
        "items": [
            {
                "session_id": session.session_id,
                "created_at": (
                    session.created_at.isoformat()
                ),
                "photo_count": session.photo_count,
                "has_collage": session.has_collage,
                "size_bytes": session.size_bytes,
            }
            for session in sessions
        ],
    }


@router.get(
    "/sessions/collages.zip"
)
def download_collages() -> StreamingResponse:
    """Download all finished collages as one ZIP archive."""

    try:
        archive_data = (
            session_archive_service
            .create_collage_archive()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    filename = (
        "fotobox-collagen-"
        + datetime.now().strftime(
            "%Y-%m-%d"
        )
        + ".zip"
    )

    return StreamingResponse(
        io.BytesIO(
            archive_data
        ),
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                'attachment; filename="'
                + filename
                + '"'
            ),
            "Cache-Control": "no-store",
        },
    )

@router.post(
    "/printer/test"
)
def printer_test() -> dict[str, str]:
    """Generate and print a diagnostic page."""

    try:
        test_image = (
            test_print_service
            .create()
        )

        job = (
            print_service
            .print_collage(
                test_image
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "submitted",
        "job": job,
        "path": str(
            test_image
        ),
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


@router.get(
    "/printer/status"
)

def printer_status() -> dict:
    """Return the current printer status."""

    return print_service.get_status()

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
    shutdown_request: ShutdownRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Request a PIN-protected system shutdown."""

    if (
        shutdown_request.pin
        != settings.admin.shutdown_pin
    ):
        logger.warning(
            "Rejected shutdown request: invalid PIN"
        )

        raise HTTPException(
            status_code=403,
            detail="Invalid shutdown PIN.",
        )

    logger.warning(
        "Shutdown requested with valid PIN"
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
        "active": (
            background_library_service
            .active_backgrounds()
        ),
    }

@router.post(
    "/backgrounds/{filename}/rotate"
)
def rotate_background(
    filename: str,
    rotation: BackgroundRotation,
) -> dict[str, str]:
    """Rotate one background image by 90 degrees."""

    try:
        background_library_service.rotate_background(
            filename=filename,
            degrees=rotation.degrees,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "rotated",
        "filename": filename,
        "degrees": str(rotation.degrees),
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
def background_settings() -> dict:
    """Return current virtual background state."""

    return {
        "enabled": (
            photo_session_service
            .backgrounds_enabled
        ),
        "selection_mode": (
            photo_session_service
            .background_selection
        ),
    }


@router.post(
    "/backgrounds/settings"
)
def update_background_settings(
    update: BackgroundModeUpdate,
) -> dict:
    """Persist and apply virtual background settings."""

    try:
        return (
            settings_admin_service
            .update_background_mode(
                enabled=update.enabled,
                selection_mode=(
                    update.selection_mode
                ),
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


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
@router.get(
    "/settings"
)
def admin_settings() -> dict:
    """Return editable Fotobox settings."""

    return (
        settings_admin_service
        .snapshot()
    )


@router.put(
    "/settings"
)
def update_admin_settings(
    update: FotoboxSettingsUpdate,
) -> dict:
    """Validate, save and apply Fotobox settings."""

    try:
        return (
            settings_admin_service
            .update(
                countdown_seconds=(
                    update.session
                    .countdown_seconds
                ),
                interval_seconds=(
                    update.session
                    .interval_seconds
                ),
                background_enabled=(
                    update.background
                    .enabled
                ),
                hue_min=(
                    update.background
                    .greenscreen
                    .hue_min
                ),
                hue_max=(
                    update.background
                    .greenscreen
                    .hue_max
                ),
                saturation_min=(
                    update.background
                    .greenscreen
                    .saturation_min
                ),
                value_min=(
                    update.background
                    .greenscreen
                    .value_min
                ),
                feather=(
                    update.background
                    .greenscreen
                    .feather
                ),
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

@router.post(
    "/greenscreen/calibrate"
)
def calibrate_greenscreen() -> dict:
    """Capture an empty greenscreen and suggest HSV settings."""

    try:
        return (
            greenscreen_calibration_service
            .calibrate()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
@router.post(
    "/greenscreen/mask"
)
def create_greenscreen_mask(
    update: GreenscreenMaskRequest,
) -> dict[str, str]:
    """Create a preview mask using supplied HSV values."""

    try:
        path = (
            greenscreen_calibration_service
            .create_mask(
                hue_min=update.hue_min,
                hue_max=update.hue_max,
                saturation_min=(
                    update.saturation_min
                ),
                value_min=(
                    update.value_min
                ),
                use_test_image=(
                    update.use_test_image
                ),
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "path": str(path),
    }

@router.post(
    "/greenscreen/test-photo"
)
def capture_greenscreen_test_photo() -> dict[str, str]:
    """Capture a person in front of the greenscreen."""

    try:
        path = (
            greenscreen_calibration_service
            .capture_test_photo()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "path": str(path),
    }

@router.get(
    "/sessions/{session_id}/collage"
)
def admin_session_collage(
    session_id: str,
) -> FileResponse:
    """Return the collage of one archived session."""

    try:
        path = (
            session_archive_service
            .get_collage_path(
                session_id
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.delete(
    "/sessions/{session_id}"
)
def delete_archived_session(
    session_id: str,
) -> dict[str, str]:
    """Delete one stored photo session."""

    try:
        session_archive_service.delete_session(
            session_id,
            protected_session_id=(
                photo_session_service
                .session_manager
                .session
                .id
            ),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "deleted",
        "session_id": session_id,
    }

@router.delete(
    "/sessions"
)
def delete_archived_sessions() -> dict:
    """Delete all stored sessions except the active one."""

    try:
        active_session_id = (
            photo_session_service
            .session_manager
            .session
            .id
        )

        deleted_count = (
            session_archive_service
            .delete_all_except(
                protected_session_id=(
                    active_session_id
                ),
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "deleted",
        "deleted_count": deleted_count,
        "protected_session_id": (
            active_session_id
        ),
    }
