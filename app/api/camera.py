import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.main import camera_service


router = APIRouter(
    prefix="/api/camera",
    tags=["camera"],
)


async def frame_generator():
    """Generate an MJPEG stream."""

    boundary = b"--frame\r\n"

    while True:
        frame = camera_service.get_latest_frame()

        if frame is not None:
            yield (
                boundary
                + b"Content-Type: image/jpeg\r\n"
                + b"Content-Length: "
                + str(len(frame)).encode()
                + b"\r\n\r\n"
                + frame
                + b"\r\n"
            )

        await asyncio.sleep(0.06)


@router.get("/stream")
async def camera_stream():
    """Return the live camera stream."""

    return StreamingResponse(
        frame_generator(),
        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
    )


@router.get("/status")
async def camera_status():
    """Return the current camera status."""

    return {
        "available": camera_service.available,
    }
