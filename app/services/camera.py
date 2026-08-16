from __future__ import annotations

import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

import cv2


class CameraError(Exception):
    """Base exception for camera errors."""


class CameraNotAvailableError(CameraError):
    """Raised when the camera cannot be opened or used."""


class CameraState(str, Enum):
    """Runtime state of the camera."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


class CameraService:
    """Manage exclusive access to the USB webcam."""

    def __init__(
        self,
        device: str = "/dev/video0",
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        jpeg_quality: int = 80,
        retry_interval: float = 2.0,
    ) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.jpeg_quality = jpeg_quality
        self.retry_interval = retry_interval

        self._capture: cv2.VideoCapture | None = None
        self._lock = threading.Lock()

        self._latest_frame: object | None = None
        self._latest_frame_jpeg: bytes | None = None

        self._last_frame_at: datetime | None = None
        self._consecutive_errors = 0
        self._last_error: str | None = None

        self._state = CameraState.STOPPED

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def state(self) -> CameraState:
        """Return the current camera state."""

        with self._lock:
            return self._state

    @property
    def available(self) -> bool:
        """Return whether the camera is currently available."""

        return self.state == CameraState.RUNNING

    @property
    def last_frame_at(self) -> datetime | None:
        """Return timestamp of last successful frame."""

        with self._lock:
            return self._last_frame_at

    @property
    def consecutive_errors(self) -> int:
        """Return number of consecutive camera errors."""

        with self._lock:
            return self._consecutive_errors

    @property
    def last_error(self) -> str | None:
        """Return most recent camera error."""

        with self._lock:
            return self._last_error

    def start(self) -> None:
        """Start camera management thread."""

        with self._lock:
            if (
                self._thread is not None
                and self._thread.is_alive()
            ):
                return

            self._state = CameraState.STARTING
            self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._camera_loop,
            name="camera-capture",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        """Stop camera management and release device."""

        self._stop_event.set()

        self._release_capture()

        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None

        with self._lock:
            self._state = CameraState.STOPPED
            self._latest_frame = None
            self._latest_frame_jpeg = None
            self._last_frame_at = None
            self._consecutive_errors = 0
            self._last_error = None

    def _camera_loop(self) -> None:
        """Open, monitor and recover the camera."""

        while not self._stop_event.is_set():

            if not self._ensure_camera_open():
                self._stop_event.wait(
                    self.retry_interval
                )
                continue

            capture = self._get_capture()

            if capture is None:
                self._stop_event.wait(
                    self.retry_interval
                )
                continue

            success, frame = capture.read()

            if not success or frame is None:
                self._handle_capture_failure(
                    "Camera returned an invalid frame."
                )

                self._release_capture()

                self._stop_event.wait(
                    self.retry_interval
                )

                continue

            success, encoded = cv2.imencode(
                ".jpg",
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    self.jpeg_quality,
                ],
            )

            if not success:
                self._handle_capture_failure(
                    "Unable to encode camera frame as JPEG."
                )
                continue

            with self._lock:
                self._latest_frame = frame.copy()
                self._latest_frame_jpeg = (
                    encoded.tobytes()
                )

                self._last_frame_at = (
                    datetime.now()
                )

                self._consecutive_errors = 0
                self._last_error = None
                self._state = CameraState.RUNNING

    def _ensure_camera_open(self) -> bool:
        """Open the camera if no active capture exists."""

        with self._lock:
            capture = self._capture

        if capture is not None and capture.isOpened():
            return True

        with self._lock:
            self._state = CameraState.STARTING

        capture = cv2.VideoCapture(
            self.device,
            cv2.CAP_V4L2,
        )

        if not capture.isOpened():
            capture.release()

            with self._lock:
                self._capture = None
                self._state = CameraState.ERROR
                self._consecutive_errors += 1
                self._last_error = (
                    f"Unable to open camera: "
                    f"{self.device}"
                )

            return False

        capture.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(
                *"MJPG"
            ),
        )

        capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            self.width,
        )

        capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            self.height,
        )

        capture.set(
            cv2.CAP_PROP_FPS,
            self.fps,
        )

        with self._lock:
            self._capture = capture
            self._latest_frame = None
            self._latest_frame_jpeg = None
            self._state = CameraState.STARTING

        return True

    def _get_capture(
        self,
    ) -> cv2.VideoCapture | None:
        """Return current VideoCapture reference."""

        with self._lock:
            return self._capture

    def _release_capture(self) -> None:
        """Release the active VideoCapture instance."""

        with self._lock:
            capture = self._capture
            self._capture = None

        if capture is not None:
            try:
                capture.release()
            except Exception:
                pass

    def _handle_capture_failure(
        self,
        message: str,
    ) -> None:
        """Record a camera failure."""

        with self._lock:
            self._consecutive_errors += 1
            self._last_error = message
            self._state = CameraState.ERROR

            self._latest_frame = None
            self._latest_frame_jpeg = None

    def get_latest_frame(
        self,
    ) -> bytes | None:
        """Return the most recent JPEG frame."""

        with self._lock:
            return self._latest_frame_jpeg

    def save_photo(
        self,
        path: Path,
    ) -> None:
        """Backward-compatible photo save method."""

        self.capture_photo(path)

    def capture_photo(
        self,
        path: Path,
    ) -> None:
        """Save the most recently acquired raw frame."""

        with self._lock:
            if self._state != CameraState.RUNNING:
                raise CameraNotAvailableError(
                    "Camera is not available."
                )

            if self._latest_frame is None:
                raise CameraNotAvailableError(
                    "No camera frame is currently available."
                )

            frame = self._latest_frame.copy()

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        success = cv2.imwrite(
            str(path),
            frame,
        )

        if not success:
            raise CameraError(
                f"Unable to save image: {path}"
            )

    def __enter__(
        self,
    ) -> CameraService:
        self.start()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.stop()

