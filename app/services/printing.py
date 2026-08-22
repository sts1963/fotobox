from __future__ import annotations

import logging
import subprocess
from pathlib import Path


logger = logging.getLogger(__name__)


class PrintError(Exception):
    """Raised when a collage cannot be printed."""


class PrintService:
    """Print completed collages through a CUPS printer queue."""

    def __init__(
        self,
        printer_name: str,
        enabled: bool = True,
    ) -> None:
        self.printer_name = printer_name
        self.enabled = enabled

    def get_status(self) -> dict:
        """Return the current physical and CUPS printer status."""

        if not self.enabled:
            return {
                "enabled": False,
                "available": False,
                "ready": False,
                "message": "Printing is disabled.",
            }

        #
        # First check whether the physical SELPHY CP510
        # is currently visible on USB.
        #
        try:
            usb_result = subprocess.run(
                [
                    "lsusb",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

        except (
            subprocess.TimeoutExpired,
            OSError,
        ) as exc:
            logger.warning(
                "Unable to query USB devices: %s",
                exc,
            )

            return {
                "enabled": True,
                "available": False,
                "ready": False,
                "message": (
                    "Unable to query USB devices: "
                    + str(exc)
                ),
            }

        if usb_result.returncode != 0:
            return {
                "enabled": True,
                "available": False,
                "ready": False,
                "message": (
                    "Unable to query USB devices."
                ),
            }

        usb_output = usb_result.stdout.lower()

        printer_connected = (
            "04a9:3128" in usb_output
            or "selphy cp510" in usb_output
        )

        if not printer_connected:
            return {
                "enabled": True,
                "available": False,
                "ready": False,
                "message": (
                    "Canon SELPHY CP510 "
                    "is not connected."
                ),
            }

        #
        # The physical printer exists.
        # Now check the CUPS queue.
        #
        try:
            result = subprocess.run(
                [
                    "lpstat",
                    "-p",
                    self.printer_name,
                    "-l",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

        except (
            subprocess.TimeoutExpired,
            OSError,
        ) as exc:
            logger.warning(
                "Unable to query printer status: %s",
                exc,
            )

            return {
                "enabled": True,
                "available": True,
                "ready": False,
                "message": str(exc),
            }

        if result.returncode != 0:
            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Printer queue is not available."
            )

            return {
                "enabled": True,
                "available": True,
                "ready": False,
                "message": message,
            }

        status = result.stdout.strip()
        status_lower = status.lower()

        ready = (
            "enabled" in status_lower
            and "disabled" not in status_lower
        )

        return {
            "enabled": True,
            "available": True,
            "ready": ready,
            "message": status,
        }

    def print_collage(
        self,
        collage_path: Path,
    ) -> str:
        """Submit one collage to CUPS."""

        if not self.enabled:
            raise PrintError(
                "Printing is disabled."
            )

        if not collage_path.exists():
            raise PrintError(
                f"Collage does not exist: {collage_path}"
            )

        status = self.get_status()

        if not status["available"]:
            raise PrintError(
                "Printer is not available."
            )

        if not status["ready"]:
            raise PrintError(
                "Printer is not ready."
            )

        command = [
            "lp",
            "-d",
            self.printer_name,
            "-o",
            "PageSize=Postcard",
            "-o",
            "ColorModel=RGB",
            "-o",
            "Resolution=300dpi",
            "-o",
            "StpBorderless=True",
            "-o",
            "StpImageType=Photo",
            str(collage_path),
        ]

        logger.info(
            "Submitting collage to printer: "
            "printer=%s collage=%s",
            self.printer_name,
            collage_path,
        )

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

        except subprocess.TimeoutExpired as exc:
            raise PrintError(
                "Printer submission timed out."
            ) from exc

        except subprocess.CalledProcessError as exc:
            message = (
                exc.stderr.strip()
                or exc.stdout.strip()
                or "Unknown CUPS error."
            )

            logger.error(
                "Unable to submit print job: %s",
                message,
            )

            raise PrintError(
                f"Unable to print collage: {message}"
            ) from exc

        except OSError as exc:
            raise PrintError(
                f"Unable to execute CUPS command: {exc}"
            ) from exc

        job_info = result.stdout.strip()

        logger.info(
            "Print job submitted: "
            "printer=%s job=%s",
            self.printer_name,
            job_info,
        )

        return job_info
