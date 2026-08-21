from __future__ import annotations
import hashlib
import io
import logging
import re
import shutil
import tempfile
from pathlib import Path

from PIL import Image


logger = logging.getLogger(__name__)


class LogoLibraryError(Exception):
    """Raised when logo library operations fail."""


class LogoLibraryService:
    """Manage uploaded and active Fotobox logos."""

    MAX_UPLOAD_BYTES = 5 * 1024 * 1024

    MAX_SIZE = (
        1200,
        1200,
    )

    def __init__(
        self,
        logo_directory: Path,
        active_logo_path: Path,
    ) -> None:
        self.logo_directory = logo_directory
        self.active_logo_path = active_logo_path

        self.logo_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.active_logo_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def list_logos(
        self,
    ) -> list[str]:
        """Return all available logo filenames."""

        result: list[str] = []

        for pattern in (
            "*.png",
            "*.jpg",
            "*.jpeg",
        ):
            result.extend(
                path.name
                for path in self.logo_directory.glob(
                    pattern
                )
            )

        return sorted(
            set(result)
        )

    def save_upload(
        self,
        filename: str,
        data: bytes,
    ) -> str:
        """Validate, resize and store an uploaded logo."""

        if not data:
            raise LogoLibraryError(
                "Uploaded file is empty."
            )

        if len(data) > self.MAX_UPLOAD_BYTES:
            raise LogoLibraryError(
                "Uploaded logo is too large."
            )

        try:
            with Image.open(
                io.BytesIO(data)
            ) as image:
                image.load()

                has_alpha = (
                    image.mode in (
                        "RGBA",
                        "LA",
                    )
                    or (
                        image.mode == "P"
                        and "transparency"
                        in image.info
                    )
                )

                if has_alpha:
                    image = image.convert(
                        "RGBA"
                    )
                    extension = ".png"
                else:
                    image = image.convert(
                        "RGB"
                    )
                    extension = ".jpg"

                image.thumbnail(
                    self.MAX_SIZE,
                    Image.Resampling.LANCZOS,
                )

        except Exception as exc:
            raise LogoLibraryError(
                "Uploaded file is not a valid image."
            ) from exc

        safe_name = self._safe_filename(
            filename,
            extension,
        )

        destination = (
            self.logo_directory
            / safe_name
        )

        self._save_atomic(
            image=image,
            destination=destination,
            extension=extension,
        )

        logger.info(
            "Logo uploaded: %s",
            destination,
        )

        return safe_name

    def select_logo(
        self,
        filename: str,
    ) -> Path:
        """Activate one logo from the library."""

        source = (
            self.logo_directory
            / Path(filename).name
        )

        if not source.is_file():
            raise LogoLibraryError(
                f"Logo does not exist: {filename}"
            )

        try:
            with Image.open(
                source
            ) as image:
                image.load()

                if image.mode not in (
                    "RGBA",
                    "LA",
                ):
                    image = image.convert(
                        "RGBA"
                    )

                self._save_atomic(
                    image=image,
                    destination=self.active_logo_path,
                    extension=".png",
                )

        except Exception as exc:
            raise LogoLibraryError(
                f"Unable to activate logo: {filename}"
            ) from exc

        logger.info(
            "Logo selected: source=%s active=%s",
            filename,
            self.active_logo_path,
        )

        return self.active_logo_path

    def active_logo_exists(
        self,
    ) -> bool:
        """Return whether an active logo currently exists."""

        return self.active_logo_path.is_file()

    @staticmethod
    def _safe_filename(
        filename: str,
        extension: str,
    ) -> str:
        """Create a safe logo filename."""

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
            stem = "logo"

        return (
            stem
            + extension
        )

    @staticmethod
    def _save_atomic(
        image: Image.Image,
        destination: Path,
        extension: str,
    ) -> None:
        """Save an image atomically."""

        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            suffix=extension,
            delete=False,
        ) as temporary:
            temporary_path = Path(
                temporary.name
            )

        try:
            if extension == ".png":
                image.save(
                    temporary_path,
                    format="PNG",
                    optimize=True,
                )
            else:
                image.save(
                    temporary_path,
                    format="JPEG",
                    quality=92,
                    optimize=True,
                )

            temporary_path.replace(
                destination
            )

        finally:
            temporary_path.unlink(
                missing_ok=True
            )

    def active_logo_name(
        self,
    ) -> str | None:
        """Return the library filename of the active logo."""

        if not self.active_logo_path.is_file():
            return None

        for filename in self.list_logos():
            path = (
                self.logo_directory
                / filename
            )

            if self._same_image(
                self.active_logo_path,
                path,
            ):
                return filename

        return None

    def delete_logo(
        self,
        filename: str,
    ) -> None:
        """Delete one unused logo."""

        safe_filename = Path(
            filename
        ).name

        if (
            safe_filename
            == self.active_logo_name()
        ):
            raise LogoLibraryError(
                "The active logo cannot be deleted."
            )

        path = (
            self.logo_directory
            / safe_filename
        )

        if not path.is_file():
            raise LogoLibraryError(
                f"Logo does not exist: {filename}"
            )

        path.unlink()

        logger.info(
            "Logo deleted: %s",
            path,
        )

    @staticmethod
    def _same_image(
        first: Path,
        second: Path,
    ) -> bool:
        """Return whether two image files contain the same pixels."""

        try:
            with Image.open(first) as first_image:
                first_image.load()

                first_rgba = first_image.convert(
                    "RGBA"
                )

            with Image.open(second) as second_image:
                second_image.load()

                second_rgba = second_image.convert(
                    "RGBA"
                )

        except Exception:
            return False

        if first_rgba.size != second_rgba.size:
            return False

        return (
            first_rgba.tobytes()
            == second_rgba.tobytes()
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

