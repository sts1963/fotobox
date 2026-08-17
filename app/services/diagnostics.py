from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from app.services.camera import CameraService
from app.services.photo_session import PhotoSessionService
from app.services.session_manager import SessionManager


class DiagnosticService:
    """Collect application and Raspberry Pi diagnostic information."""

    def __init__(
        self,
        camera_service: CameraService,
        session_manager: SessionManager,
        photo_session_service: PhotoSessionService,
        data_path: Path,
        log_path: Path,
    ) -> None:
        self.camera_service = camera_service
        self.session_manager = session_manager
        self.photo_session_service = photo_session_service
        self.data_path = data_path
        self.log_path = log_path

        self._started_at = time.monotonic()

    def snapshot(self) -> dict[str, Any]:
        """Return a complete diagnostic snapshot."""

        return {
            "application": self._application_status(),
            "camera": self._camera_status(),
            "session": self._session_status(),
            "system": self._system_status(),
        }

    def _application_status(self) -> dict[str, Any]:
        """Return application runtime information."""

        return {
            "status": "running",
            "uptime_seconds": round(
                time.monotonic() - self._started_at,
                1,
            ),
        }

    def _camera_status(self) -> dict[str, Any]:
        """Return camera diagnostic information."""

        last_frame_at = (
            self.camera_service.last_frame_at
        )

        return {
            "state": self.camera_service.state.value,
            "available": self.camera_service.available,
            "last_frame_at": (
                last_frame_at.isoformat()
                if last_frame_at is not None
                else None
            ),
            "consecutive_errors": (
                self.camera_service.consecutive_errors
            ),
            "last_error": (
                self.camera_service.last_error
            ),
        }

    def _session_status(self) -> dict[str, Any]:
        """Return current photobox session information."""

        session = self.session_manager.session

        return {
            "id": session.id,
            "state": session.state.value,
            "running": self.photo_session_service.running,
            "created_at": session.created_at.isoformat(),
            "photo_count": len(session.photos),
            "collage": session.collage,
            "error": session.error,
        }

    def _system_status(self) -> dict[str, Any]:
        """Return Raspberry Pi / Linux system information."""

        return {
            "system_uptime_seconds": (
                self._read_system_uptime()
            ),
            "cpu_temperature_c": (
                self._read_cpu_temperature()
            ),
            "disk": self._read_disk_usage(),
        }

    @staticmethod
    def _read_system_uptime() -> float | None:
        """Read Linux system uptime from /proc."""

        try:
            text = Path(
                "/proc/uptime"
            ).read_text(
                encoding="utf-8"
            )

            return round(
                float(text.split()[0]),
                1,
            )

        except (
            OSError,
            ValueError,
            IndexError,
        ):
            return None

    @staticmethod
    def _read_cpu_temperature() -> float | None:
        """Read Raspberry Pi CPU temperature."""

        temperature_paths = [
            Path(
                "/sys/class/thermal/"
                "thermal_zone0/temp"
            ),
            Path(
                "/sys/devices/virtual/thermal/"
                "thermal_zone0/temp"
            ),
        ]

        for path in temperature_paths:
            try:
                value = float(
                    path.read_text(
                        encoding="utf-8"
                    ).strip()
                )

                return round(
                    value / 1000.0,
                    1,
                )

            except (
                OSError,
                ValueError,
            ):
                continue

        return None

    def get_log_lines(
        self,
        limit: int = 100,
    ) -> list[str]:
        """Return the last lines from the Fotobox log."""

        limit = max(
            1,
            min(limit, 500),
        )

        try:
            lines = self.log_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()

        except OSError:
            return []

        return lines[-limit:]

    def _read_disk_usage(
        self,
    ) -> dict[str, Any]:
        """Return disk usage for the Fotobox data filesystem."""

        try:
            usage = shutil.disk_usage(
                self.data_path
            )

        except OSError:
            return {
                "total_gb": None,
                "used_gb": None,
                "free_gb": None,
                "used_percent": None,
            }

        total_gb = (
            usage.total
            / (1024 ** 3)
        )

        used_gb = (
            usage.used
            / (1024 ** 3)
        )

        free_gb = (
            usage.free
            / (1024 ** 3)
        )

        used_percent = (
            (usage.used / usage.total) * 100
            if usage.total > 0
            else 0
        )

        return {
            "total_gb": round(total_gb, 1),
            "used_gb": round(used_gb, 1),
            "free_gb": round(free_gb, 1),
            "used_percent": round(
                used_percent,
                1,
            ),
        }
