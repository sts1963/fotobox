from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.container import camera_service
from app.services.stream import mjpeg_stream

router = APIRouter(prefix="/api")

@router.get("/camera/stream")
def camera_stream() -> StreamingResponse:
    """Return the live camera stream."""

    return StreamingResponse(
        mjpeg_stream(camera_service),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

@router.get("/health")
async def health() -> dict[str, str]:
    """Return a basic application health status."""

    return {
        "status": "ok",
        "service": "fotobox",
    }
