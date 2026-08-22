from __future__ import annotations

from pathlib import Path

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


class TestPrintService:
    """Generate a diagnostic print image."""

    def __init__(
        self,
        output_path: Path,
        width: int = 1800,
        height: int = 1200,
        margin: int = 60,
    ) -> None:
        self.output_path = output_path
        self.width = width
        self.height = height
        self.margin = margin

    def create(self) -> Path:
        """Create a diagnostic JPEG for printer testing."""

        image = Image.new(
            "RGB",
            (
                self.width,
                self.height,
            ),
            "white",
        )

        draw = ImageDraw.Draw(
            image
        )

        #
        # Outer safety rectangle.
        #
        draw.rectangle(
            (
                self.margin,
                self.margin,
                self.width - self.margin - 1,
                self.height - self.margin - 1,
            ),
            outline="black",
            width=6,
        )

        #
        # Center cross.
        #
        center_x = (
            self.width // 2
        )

        center_y = (
            self.height // 2
        )

        draw.line(
            (
                center_x,
                self.margin,
                center_x,
                self.height - self.margin,
            ),
            fill="black",
            width=3,
        )

        draw.line(
            (
                self.margin,
                center_y,
                self.width - self.margin,
                center_y,
            ),
            fill="black",
            width=3,
        )

        #
        # Color patches.
        #
        patch_width = 220
        patch_height = 120
        patch_gap = 20

        colors = [
            ("Red", (255, 0, 0)),
            ("Green", (0, 255, 0)),
            ("Blue", (0, 0, 255)),
            ("Cyan", (0, 255, 255)),
            ("Magenta", (255, 0, 255)),
            ("Yellow", (255, 255, 0)),
        ]

        total_width = (
            len(colors) * patch_width
            + (
                len(colors) - 1
            ) * patch_gap
        )

        start_x = (
            self.width
            - total_width
        ) // 2

        patch_y = 180

        for index, (
            label,
            color,
        ) in enumerate(colors):
            x = (
                start_x
                + index
                * (
                    patch_width
                    + patch_gap
                )
            )

            draw.rectangle(
                (
                    x,
                    patch_y,
                    x + patch_width,
                    patch_y + patch_height,
                ),
                fill=color,
                outline="black",
                width=3,
            )

            draw.text(
                (
                    x + 10,
                    patch_y
                    + patch_height
                    + 8,
                ),
                label,
                fill="black",
            )

        #
        # Greyscale strip.
        #
        grey_y = 520
        grey_width = 160

        for index in range(11):
            level = int(
                255
                * index
                / 10
            )

            x = (
                self.margin
                + index
                * grey_width
            )

            draw.rectangle(
                (
                    x,
                    grey_y,
                    x + grey_width,
                    grey_y + 120,
                ),
                fill=(
                    level,
                    level,
                    level,
                ),
                outline="black",
            )

        #
        # Diagnostic text.
        #
        text = (
            "FOTOBOX TESTDRUCK\n"
            "Canon SELPHY CP510\n"
            "Postcard 100 x 148 mm\n"
            "1800 x 1200 px / 300 dpi"
        )

        draw.multiline_text(
            (
                self.margin + 30,
                760,
            ),
            text,
            fill="black",
            spacing=12,
        )

        #
        # Corner markers make asymmetric cropping obvious.
        #
        marker_size = 50

        corners = [
            (
                self.margin,
                self.margin,
            ),
            (
                self.width
                - self.margin
                - marker_size,
                self.margin,
            ),
            (
                self.margin,
                self.height
                - self.margin
                - marker_size,
            ),
            (
                self.width
                - self.margin
                - marker_size,
                self.height
                - self.margin
                - marker_size,
            ),
        ]

        for x, y in corners:
            draw.rectangle(
                (
                    x,
                    y,
                    x + marker_size,
                    y + marker_size,
                ),
                fill="black",
            )

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        image.save(
            self.output_path,
            format="JPEG",
            quality=95,
            subsampling=0,
            dpi=(
                300,
                300,
            ),
        )

        return self.output_path
