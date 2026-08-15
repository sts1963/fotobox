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
    ) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.jpeg_quality = jpeg_quality

        self._capture: cv2.VideoCapture | None = None
        self._lock = threading.Lock()

        # Latest raw OpenCV frame.
        self._latest_frame: object | None = None

        # Latest JPEG representation for the live stream.
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
        """Return the timestamp of the last successfully acquired frame."""

        with self._lock:
            return self._last_frame_at

    @property
    def consecutive_errors(self) -> int:
        """Return the number of consecutive frame acquisition errors."""

        with self._lock:
            return self._consecutive_errors

    @property
    def last_error(self) -> str | None:
        """Return the most recent camera error."""

        with self._lock:
            return self._last_error

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
                self._last_error = (
                    f"Unable to open camera: {self.device}"
                )

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
            self._latest_frame_jpeg = None
            self._last_frame_at = None
            self._consecutive_errors = 0
            self._last_error = None
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
            self._latest_frame_jpeg = None
            self._last_frame_at = None
            self._consecutive_errors = 0
            self._last_error = None

        if capture is not None:
            capture.release()

        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _capture_loop(self) -> None:
        """Continuously acquire frames from the camera."""

        while not self._stop_event.is_set():
            with self._lock:
                capture = self._capture

            if capture is None:
                break

            success, frame = capture.read()

            if not success or frame is None:
                self._handle_capture_error(
                    "Camera returned an invalid frame."
                )
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
                self._handle_capture_error(
                    "Unable to encode camera frame as JPEG."
                )
                continue

            with self._lock:
                self._latest_frame = frame.copy()
                self._latest_frame_jpeg = encoded.tobytes()
                self._last_frame_at = datetime.now()
                self._consecutive_errors = 0
                self._last_error = None

                if self._state == CameraState.ERROR:
                    self._state = CameraState.RUNNING

    def _handle_capture_error(
        self,
        message: str = "Camera returned an invalid frame.",
    ) -> None:
        """Record a frame acquisition error."""

        with self._lock:
            self._consecutive_errors += 1
            self._last_error = message

            if self._state == CameraState.RUNNING:
                self._state = CameraState.ERROR

    def get_latest_frame(self) -> bytes | None:
        """Return the most recent JPEG frame."""

        with self._lock:
            return self._latest_frame_jpeg

    def save_photo(self, path: Path) -> None:
        """
        Save the current camera frame.

        Kept for backwards compatibility with the existing API.
        The actual capture is handled by capture_photo().
        """

        self.capture_photo(path)

    def capture_photo(self, path: Path) -> None:
        """
        Save the most recently acquired raw camera frame.

        The camera capture thread is the only component that calls
        VideoCapture.read(). This method only accesses the latest
        already-acquired frame.
        """

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
