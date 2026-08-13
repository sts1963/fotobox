from __future__ import annotations

import threading
import time
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
    ) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.jpeg_quality = jpeg_quality

        self._capture: cv2.VideoCapture | None = None
        self._lock = threading.Lock()

        self._latest_frame: bytes | None = None

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

    def start(self) -> None:
        """Open the camera and start frame acquisition."""

        with self._lock:
            if self._state == CameraState.RUNNING:
                return

            self._state = CameraState.STARTING

        capture = cv2.VideoCapture(
            self.device,
            cv2.CAP_V4L2,
        )

        if not capture.isOpened():
            capture.release()

            with self._lock:
                self._state = CameraState.ERROR

            raise CameraNotAvailableError(
                f"Unable to open camera: {self.device}"
            )

        # Request the format supported by the C920.
        capture.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(*"MJPG"),
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
            self._stop_event.clear()
            self._state = CameraState.RUNNING

        self._thread = threading.Thread(
            target=self._capture_loop,
            name="camera-capture",
            daemon=True,
        )

        self._thread.start()

    def stop(self) -> None:
        """Stop frame acquisition and release the camera."""

        self._stop_event.set()

        with self._lock:
            capture = self._capture
            self._capture = None
            self._state = CameraState.STOPPED
            self._latest_frame = None

        if capture is not None:
            capture.release()

        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _capture_loop(self) -> None:
        """Continuously acquire and encode frames."""

        while not self._stop_event.is_set():
            with self._lock:
                capture = self._capture

            if capture is None:
                break

            success, frame = capture.read()

            if not success or frame is None:
                self._handle_capture_error()
                time.sleep(0.1)
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
                continue

            with self._lock:
                self._latest_frame = encoded.tobytes()

                if self._state == CameraState.ERROR:
                    self._state = CameraState.RUNNING

    def _handle_capture_error(self) -> None:
        """Mark the camera as unavailable after a failed frame read."""

        with self._lock:
            if self._state == CameraState.RUNNING:
                self._state = CameraState.ERROR

    def get_latest_frame(self) -> bytes | None:
        """Return the most recently acquired JPEG frame."""

        with self._lock:
            return self._latest_frame

    def save_photo(self, path: Path) -> None:
        """Capture and save one photo."""

        with self._lock:
            capture = self._capture

            if (
                capture is None
                or self._state != CameraState.RUNNING
            ):
                raise CameraNotAvailableError(
                    "Camera is not available."
                )

            success, frame = capture.read()

        if not success or frame is None:
            self._handle_capture_error()

            raise CameraNotAvailableError(
                "Camera returned an invalid frame."
            )

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

    def __enter__(self) -> CameraService:
        self.start()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.stop()

