```python
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


def test_camera_requires_valid_device() -> None:
    camera = CameraService(
        device="/dev/this-camera-does-not-exist"
    )

    with pytest.raises(CameraNotAvailableError):
        camera.start()

    assert camera.state == CameraState.ERROR


def test_photo_requires_running_camera(
    tmp_path: Path,
) -> None:
    camera = CameraService()

    with pytest.raises(CameraNotAvailableError):
        camera.save_photo(
            tmp_path / "photo.jpg"
        )
```

