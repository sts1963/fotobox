from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.container import camera_service
from app.services.stream import mjpeg_stream

from pathlib import Path
from app.services.container import camera_service

router = APIRouter()
router = APIRouter(prefix="/api")

@router.post("/camera/test-photo")
def test_photo() -> dict:
    """Capture a test photo using the running camera service."""

    output = Path("/tmp/fotobox-test.jpg")

    camera_service.capture_photo(output)

    return {
        "success": True,
        "path": str(output),
        "size": output.stat().st_size,
    }

@router.get("/camera/stream")
def camera_stream() -> StreamingResponse:
    """Return the live camera stream."""

    return StreamingResponse(
        mjpeg_stream(camera_service),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

@router.get("/camera/status")
def camera_status() -> dict:
    """Return the current camera status."""

    return {
        "state": camera_service.state.value,
        "available": camera_service.available,
        "last_frame_at": (
            camera_service.last_frame_at.isoformat()
            if camera_service.last_frame_at is not None
            else None
        ),
        "consecutive_errors": camera_service.consecutive_errors,
        "last_error": camera_service.last_error,
    }

@router.get("/health")
async def health() -> dict[str, str]:
    """Return a basic application health status."""

    return {
        "status": "ok",
        "service": "fotobox",
    }
