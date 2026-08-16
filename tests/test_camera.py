from pathlib import Path

import pytest

from app.services.camera import (
    CameraNotAvailableError,
    CameraService,
    CameraState,
)


def test_camera_initially_stopped() -> None:
    camera = CameraService()

    assert camera.state == CameraState.STOPPED
    assert camera.available is False


def test_camera_invalid_device_enters_error() -> None:
    camera = CameraService(
        device="/dev/this-camera-does-not-exist",
        retry_interval=0.05,
    )

    camera.start()

    import time

    deadline = time.time() + 1.0

    while (
        camera.state != CameraState.ERROR
        and time.time() < deadline
    ):
        time.sleep(0.01)

    assert camera.state == CameraState.ERROR
    assert camera.available is False
    assert camera.last_error is not None

    camera.stop()

    assert camera.state == CameraState.STOPPED

def test_photo_requires_running_camera(
    tmp_path: Path,
) -> None:
    camera = CameraService()

    with pytest.raises(CameraNotAvailableError):
        camera.save_photo(
            tmp_path / "photo.jpg"
        )

def test_capture_photo_without_running_camera(
    tmp_path: Path,
) -> None:
    camera = CameraService()

    with pytest.raises(CameraNotAvailableError):
        camera.capture_photo(
            tmp_path / "photo.jpg"
        )

