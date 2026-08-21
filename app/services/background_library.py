from __future__ import annotations
import hashlib
import io
import logging
import re
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


logger = logging.getLogger(__name__)


class BackgroundLibraryError(Exception):
    """Raised when background library operations fail."""


class BackgroundLibraryService:
    """Manage uploaded and active virtual backgrounds."""

    MAX_UPLOAD_BYTES = 10 * 1024 * 1024

    TARGET_SIZE = (
        1920,
        1080,
    )

    def __init__(
        self,
        background_directory: Path,
    ) -> None:
        self.background_directory = (
            background_directory
        )

        self.library_directory = (
            background_directory / "library"
        )

        self.library_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def list_backgrounds(
        self,
    ) -> list[str]:
        """Return all available background filenames."""

        return sorted(
            path.name
            for path in self.library_directory.glob(
                "*.jpg"
            )
        )

    def save_upload(
        self,
        filename: str,
        data: bytes,
    ) -> str:
        """Validate, normalize and store an uploaded image."""

        if not data:
            raise BackgroundLibraryError(
                "Uploaded file is empty."
            )

        if len(data) > self.MAX_UPLOAD_BYTES:
            raise BackgroundLibraryError(
                "Uploaded image is too large."
            )

        safe_name = self._safe_filename(
            filename
        )

        try:
            with Image.open(
                io.BytesIO(data)
            ) as image:
                image.load()

                image = image.convert(
                    "RGB"
                )

                image = ImageOps.fit(
                    image,
                    self.TARGET_SIZE,
                    method=Image.Resampling.LANCZOS,
                )

        except Exception as exc:
            raise BackgroundLibraryError(
                "Uploaded file is not a valid image."
            ) from exc

        destination = (
            self.library_directory
            / safe_name
        )

        self._save_atomic(
            image,
            destination,
        )

        logger.info(
            "Background uploaded: %s",
            destination,
        )

        return safe_name

    def select_background(
        self,
        slot: int,
        filename: str,
    ) -> Path:
        """Assign one library image to photo slot 1..3."""

        if slot not in (
            1,
            2,
            3,
        ):
            raise BackgroundLibraryError(
                "Background slot must be 1, 2 or 3."
            )

        source = (
            self.library_directory
            / Path(filename).name
        )

        if not source.is_file():
            raise BackgroundLibraryError(
                f"Background does not exist: {filename}"
            )

        destination = (
            self.background_directory
            / f"background_{slot:02d}.jpg"
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            suffix=".jpg",
            delete=False,
        ) as temporary:
            temporary_path = Path(
                temporary.name
            )

        try:
            shutil.copyfile(
                source,
                temporary_path,
            )

            temporary_path.replace(
                destination
            )

        finally:
            temporary_path.unlink(
                missing_ok=True
            )

        logger.info(
            "Background selected: slot=%s source=%s",
            slot,
            filename,
        )

        return destination

    @staticmethod
    def _safe_filename(
        filename: str,
    ) -> str:
        """Create a safe JPEG filename."""

        stem = Path(
            filename
        ).stem.strip().lower()

        stem = re.sub(
            r"[^a-z0-9_-]+",
            "-",
            stem,
        )

        stem = stem.strip(
            "-"
        )

        if not stem:
            stem = "background"

        return f"{stem}.jpg"

    @staticmethod
    def _save_atomic(
        image: Image.Image,
        destination: Path,
    ) -> None:
        """Save an image without exposing a partial file."""

        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            suffix=".jpg",
            delete=False,
        ) as temporary:
            temporary_path = Path(
                temporary.name
            )

        try:
            image.save(
                temporary_path,
                format="JPEG",
                quality=90,
                optimize=True,
            )

            temporary_path.replace(
                destination
            )

        finally:
            temporary_path.unlink(
                missing_ok=True
            )

    def active_backgrounds(
        self,
    ) -> dict[int, str | None]:
        """Return the library image assigned to each slot."""

        result: dict[int, str | None] = {}

        library_files = {
            path.name: path
            for path in self.library_directory.glob(
                "*.jpg"
            )
        }

        for slot in (
            1,
            2,
            3,
        ):
            active_path = (
                self.background_directory
                / f"background_{slot:02d}.jpg"
            )

            if not active_path.is_file():
                result[slot] = None
                continue

            active_hash = self._file_hash(
                active_path
            )

            result[slot] = None

            for (
                filename,
                library_path,
            ) in library_files.items():
                if (
                    self._file_hash(
                        library_path
                    )
                    == active_hash
                ):
                    result[slot] = filename
                    break

        return result

    def delete_background(
        self,
        filename: str,
    ) -> None:
        """Delete an unused image from the library."""

        safe_filename = Path(
            filename
        ).name

        path = (
            self.library_directory
            / safe_filename
        )

        if not path.is_file():
            raise BackgroundLibraryError(
                f"Background does not exist: {filename}"
            )

        active = self.active_backgrounds()

        if safe_filename in active.values():
            raise BackgroundLibraryError(
                "An active background cannot be deleted."
            )

        path.unlink()

        logger.info(
            "Background deleted: %s",
            path,
        )

    @staticmethod
    def _file_hash(
        path: Path,
    ) -> str:
        """Return SHA-256 hash of a file."""

        digest = hashlib.sha256()

        with path.open(
            "rb"
        ) as file:
            for block in iter(
                lambda: file.read(65536),
                b"",
            ):
                digest.update(
                    block
                )

        return digest.hexdigest()

