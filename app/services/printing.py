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

        self._recovery_error: str | None = None

    def get_status(self) -> dict:
        """Return the current physical and CUPS printer status."""

        if not self.enabled:
            return {
                "enabled": False,
                "available": False,
                "ready": False,
                "message": "Printing is disabled.",
            }

        usb_status = self._check_usb()

        if not usb_status["available"]:
            return usb_status

        cups_status = self._get_cups_status()

        if cups_status["disabled"]:
            error_state = cups_status["message"]

            if (
                self._recovery_error
                != error_state
            ):
                self._recovery_error = (
                    error_state
                )

                logger.warning(
                    "Printer queue disabled, "
                    "attempting automatic recovery: %s",
                    self.printer_name,
                )

                recovery = (
                    self._recover_queue()
                )

                if recovery["success"]:
                    cups_status = (
                        self._get_cups_status()
                    )

                    if cups_status["ready"]:
                        self._recovery_error = None

                        cups_status["message"] = (
                            "Printer queue recovered "
                            "automatically."
                        )

        else:
            self._recovery_error = None

        return {
            "enabled": True,
            "available": True,
            "ready": cups_status["ready"],
            "message": cups_status["message"],
        }

    def _check_usb(
        self,
    ) -> dict:
        """Check whether the SELPHY CP510 is visible on USB."""

        try:
            result = subprocess.run(
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

        if result.returncode != 0:
            return {
                "enabled": True,
                "available": False,
                "ready": False,
                "message": (
                    "Unable to query USB devices."
                ),
            }

        usb_output = (
            result.stdout.lower()
        )

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

        return {
            "enabled": True,
            "available": True,
            "ready": True,
            "message": (
                "Canon SELPHY CP510 connected."
            ),
        }

    def _get_cups_status(
        self,
    ) -> dict:
        """Return the current CUPS queue status."""

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
                "ready": False,
                "disabled": False,
                "message": str(exc),
            }

        if result.returncode != 0:
            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Printer queue is not available."
            )

            return {
                "ready": False,
                "disabled": False,
                "message": message,
            }

        status = result.stdout.strip()
        status_lower = (
            status.lower()
        )

        disabled = (
            "disabled" in status_lower
        )

        ready = (
            "enabled" in status_lower
            and not disabled
        )

        return {
            "ready": ready,
            "disabled": disabled,
            "message": status,
        }

    def _recover_queue(
        self,
    ) -> dict:
        """Discard failed jobs and re-enable the CUPS queue."""

        commands = [
            [
                "cancel",
                "-a",
                self.printer_name,
            ],
            [
                "cupsenable",
                self.printer_name,
            ],
            [
                "cupsaccept",
                self.printer_name,
            ],
        ]

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )

            except (
                subprocess.TimeoutExpired,
                OSError,
            ) as exc:
                logger.error(
                    "Printer recovery command failed: "
                    "command=%s error=%s",
                    command,
                    exc,
                )

                return {
                    "success": False,
                    "message": str(exc),
                }

            if result.returncode != 0:
                message = (
                    result.stderr.strip()
                    or result.stdout.strip()
                    or "Unknown CUPS error."
                )

                logger.error(
                    "Printer recovery command failed: "
                    "command=%s error=%s",
                    command,
                    message,
                )

                return {
                    "success": False,
                    "message": message,
                }

        logger.warning(
            "Printer queue recovered: "
            "printer=%s pending jobs discarded",
            self.printer_name,
        )

        return {
            "success": True,
            "message": (
                "Printer queue recovered."
            ),
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

        job_info = (
            result.stdout.strip()
        )

        logger.info(
            "Print job submitted: "
            "printer=%s job=%s",
            self.printer_name,
            job_info,
        )

        return job_info
