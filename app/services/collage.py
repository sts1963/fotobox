from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.services.image_processing import (
    ImageProcessingError,
    ImageProcessor,
)


class CollageError(Exception):
    """Raised when a collage cannot be generated."""


class CollageGenerator:
    """Generate photobooth collages."""

    def __init__(
        self,
        width: int = 1800,
        height: int = 1200,
        gap: int = 24,
        margin: int = 24,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(
                "Collage dimensions must be greater than zero."
            )

        if gap < 0 or margin < 0:
            raise ValueError(
                "Gap and margin must not be negative."
            )

        self.width = width
        self.height = height
        self.gap = gap
        self.margin = margin

        self.processor = ImageProcessor()

    def create_grid_2x2(
        self,
        photo_paths: list[Path],
        output_path: Path,
        logo_path: Path | None = None,
    ) -> Path:
        """Create a 2x2 collage from three photos and an optional logo."""

        if len(photo_paths) != 3:
            raise CollageError(
                "Exactly three photos are required for the 2x2 layout."
            )

        content_width = (
            self.width
            - (2 * self.margin)
            - self.gap
        )

        content_height = (
            self.height
            - (2 * self.margin)
            - self.gap
        )

        cell_width = content_width // 2
        cell_height = content_height // 2

        if cell_width <= 0 or cell_height <= 0:
            raise CollageError(
                "Collage dimensions are too small."
            )

        canvas = Image.new(
            "RGB",
            (self.width, self.height),
            "white",
        )

        positions = [
            (
                self.margin,
                self.margin,
            ),
            (
                self.margin + cell_width + self.gap,
                self.margin,
            ),
            (
                self.margin,
                self.margin + cell_height + self.gap,
            ),
        ]

        for photo_path, position in zip(
            photo_paths,
            positions,
            strict=True,
        ):
            try:
                image = self.processor.open_image(
                    str(photo_path)
                )
            except ImageProcessingError as exc:
                raise CollageError(
                    f"Unable to use photo: {photo_path}"
                ) from exc

            fitted = self.processor.fit_center_crop(
                image,
                cell_width,
                cell_height,
            )

            canvas.paste(
                fitted,
                position,
            )

        logo_x = (
            self.margin
            + cell_width
            + self.gap
        )

        logo_y = (
            self.margin
            + cell_height
            + self.gap
        )

        if logo_path is not None and logo_path.exists():
            self._place_logo(
                canvas=canvas,
                logo_path=logo_path,
                x=logo_x,
                y=logo_y,
                width=cell_width,
                height=cell_height,
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            canvas.save(
                output_path,
                format="JPEG",
                quality=95,
                subsampling=0,
                dpi=(300, 300),
            )
        except Exception as exc:
            raise CollageError(
                f"Unable to save collage: {output_path}"
            ) from exc

        return output_path

    def _place_logo(
        self,
        canvas: Image.Image,
        logo_path: Path,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """Place an optional logo centered in one collage cell."""

        try:
            logo = Image.open(logo_path)
            logo.load()
        except Exception as exc:
            raise CollageError(
                f"Unable to open logo: {logo_path}"
            ) from exc

        if logo.mode not in ("RGBA", "LA"):
            logo = logo.convert("RGBA")

        padding = 60

        max_width = max(
            1,
            width - 2 * padding,
        )

        max_height = max(
            1,
            height - 2 * padding,
        )

        logo.thumbnail(
            (max_width, max_height),
            Image.Resampling.LANCZOS,
        )

        paste_x = (
            x
            + (width - logo.width) // 2
        )

        paste_y = (
            y
            + (height - logo.height) // 2
        )

        canvas.paste(
            logo,
            (paste_x, paste_y),
            logo,
        )

