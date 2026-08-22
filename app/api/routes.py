from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
)

from app.services.container import (
    camera_service,
    session_manager,
    greenscreen_calibration_service,
)
from app.services.stream import mjpeg_stream


router = APIRouter(
    prefix="/api"
)


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a basic application health status."""

    return {
        "status": "ok",
        "service": "fotobox",
    }


@router.get("/camera/stream")
def camera_stream() -> StreamingResponse:
    """Return the live camera stream."""

    return StreamingResponse(
        mjpeg_stream(
            camera_service
        ),
        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
    )


@router.get("/camera/status")
def camera_status() -> dict:
    """Return the current camera status."""

    return {
        "state": (
            camera_service.state.value
        ),
        "available": (
            camera_service.available
        ),
        "last_frame_at": (
            camera_service
            .last_frame_at
            .isoformat()
            if (
                camera_service
                .last_frame_at
                is not None
            )
            else None
        ),
        "consecutive_errors": (
            camera_service
            .consecutive_errors
        ),
        "last_error": (
            camera_service.last_error
        ),
    }


@router.post("/camera/test-photo")
def test_photo() -> dict:
    """Capture a test photo using the running camera service."""

    output = Path(
        "/tmp/fotobox-test.jpg"
    )

    camera_service.capture_photo(
        output
    )

    return {
        "success": True,
        "path": str(output),
        "size": output.stat().st_size,
    }


@router.get(
    "/session/{session_id}/photo/{number}"
)
def session_photo(
    session_id: str,
    number: int,
) -> FileResponse:
    """Return one captured photo of the current session."""

    session = (
        session_manager.session
    )

    if session.id != session_id:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    if (
        number < 1
        or number > len(session.photos)
    ):
        raise HTTPException(
            status_code=404,
            detail="Photo not available.",
        )

    photo_path = Path(
        session.photos[
            number - 1
        ]
    )

    if (
        not photo_path.exists()
        or not photo_path.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="Photo file not found.",
        )

    return FileResponse(
        photo_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/session/{session_id}/collage"
)
def session_collage(
    session_id: str,
) -> FileResponse:
    """Return the collage belonging to the current session."""

    session = (
        session_manager.session
    )

    if session.id != session_id:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    if session.collage is None:
        raise HTTPException(
            status_code=404,
            detail="Collage is not available.",
        )

    collage_path = Path(
        session.collage
    )

    if (
        not collage_path.exists()
        or not collage_path.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="Collage file not found.",
        )

    return FileResponse(
        collage_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
        },
    )

@router.get(
    "/greenscreen/calibration/reference"
)
def greenscreen_reference() -> FileResponse:
    """Return the latest greenscreen calibration image."""

    path = (
        greenscreen_calibration_service
        .calibration_directory
        / "greenscreen_reference.jpg"
    )

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Calibration image not found.",
        )

    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/greenscreen/calibration/mask"
)
def greenscreen_mask() -> FileResponse:
    """Return the latest greenscreen calibration mask."""

    path = (
        greenscreen_calibration_service
        .calibration_directory
        / "greenscreen_mask.png"
    )

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Calibration mask not found.",
        )

    return FileResponse(
        path,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
        },
    )

@router.get(
    "/greenscreen/calibration/test"
)
def greenscreen_test_image() -> FileResponse:
    """Return the latest greenscreen test image."""

    path = (
        greenscreen_calibration_service
        .calibration_directory
        / "greenscreen_test.jpg"
    )

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Greenscreen test image not found.",
        )

    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/greenscreen/calibration/test-mask"
)
def greenscreen_test_mask() -> FileResponse:
    """Return the latest greenscreen test mask."""

    path = (
        greenscreen_calibration_service
        .calibration_directory
        / "greenscreen_test_mask.png"
    )

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Greenscreen test mask not found.",
        )

    return FileResponse(
        path,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
        },
    )
