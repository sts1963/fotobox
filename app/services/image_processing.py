from __future__ import annotations

from PIL import Image, ImageOps


class ImageProcessingError(Exception):
    """Raised when an image cannot be processed."""


class ImageProcessor:
    """Provide reusable image preparation operations."""

    @staticmethod
    def open_image(path: str) -> Image.Image:
        """Open an image and normalize EXIF orientation."""

        try:
            image = Image.open(path)
            image.load()
        except Exception as exc:
            raise ImageProcessingError(
                f"Unable to open image: {path}"
            ) from exc

        image = ImageOps.exif_transpose(image)

        return image.convert("RGB")

    @staticmethod
    def fit_center_crop(
        image: Image.Image,
        width: int,
        height: int,
    ) -> Image.Image:
        """
        Resize and center-crop an image to the requested dimensions.

        The image keeps its aspect ratio and is never distorted.
        """

        if width <= 0 or height <= 0:
            raise ValueError(
                "Target width and height must be greater than zero."
            )

        return ImageOps.fit(
            image,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

    @staticmethod
    def fit_contain(
        image: Image.Image,
        width: int,
        height: int,
    ) -> Image.Image:
        """
        Scale an image proportionally so it completely fits inside
        the requested dimensions.
        """

        if width <= 0 or height <= 0:
            raise ValueError(
                "Target width and height must be greater than zero."
            )

        copy = image.copy()

        copy.thumbnail(
            (width, height),
            Image.Resampling.LANCZOS,
        )

        return copy

