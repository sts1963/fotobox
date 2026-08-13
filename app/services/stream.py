from __future__ import annotations

import time
from collections.abc import Generator

from app.services.camera import CameraService


BOUNDARY = b"frame"


def mjpeg_stream(
    camera: CameraService,
    frame_interval: float = 1 / 15,
) -> Generator[bytes, None, None]:
    """
    Generate an MJPEG HTTP stream from the camera.

    The generator yields complete multipart frames suitable
    for an HTTP multipart/x-mixed-replace response.
    """

    while True:
        frame = camera.get_latest_frame()

        if frame is None:
            time.sleep(0.1)
            continue

        yield (
            b"--"
            + BOUNDARY
            + b"\r\n"
            + b"Content-Type: image/jpeg\r\n"
            + f"Content-Length: {len(frame)}".encode()
            + b"\r\n"
            + b"\r\n"
            + frame
            + b"\r\n"
        )

        time.sleep(frame_interval)

