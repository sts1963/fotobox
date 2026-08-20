from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np


logger = logging.getLogger(__name__)


class BackgroundProcessingError(Exception):
    """Raised when virtual background processing fails."""


class BackgroundProcessor:
    """Replace a greenscreen background with another image."""

    def __init__(
        self,
        hue_min: int = 35,
        hue_max: int = 90,
        saturation_min: int = 60,
        value_min: int = 40,
        feather: int = 5,
    ) -> None:
        self.hue_min = hue_min
        self.hue_max = hue_max
        self.saturation_min = saturation_min
        self.value_min = value_min
        self.feather = feather

    def replace_greenscreen(
        self,
        photo_path: Path,
        background_path: Path,
        output_path: Path,
    ) -> Path:
        """Replace green areas in a photo with a virtual background."""

        foreground = cv2.imread(
            str(photo_path),
            cv2.IMREAD_COLOR,
        )

        if foreground is None:
            raise BackgroundProcessingError(
                f"Unable to read photo: {photo_path}"
            )

        background = cv2.imread(
            str(background_path),
            cv2.IMREAD_COLOR,
        )

        if background is None:
            raise BackgroundProcessingError(
                f"Unable to read background: {background_path}"
            )

        height, width = foreground.shape[:2]

        background = self._cover_resize(
            background,
            width,
            height,
        )

        hsv = cv2.cvtColor(
            foreground,
            cv2.COLOR_BGR2HSV,
        )

        lower = np.array(
            [
                self.hue_min,
                self.saturation_min,
                self.value_min,
            ],
            dtype=np.uint8,
        )

        upper = np.array(
            [
                self.hue_max,
                255,
                255,
            ],
            dtype=np.uint8,
        )

        green_mask = cv2.inRange(
            hsv,
            lower,
            upper,
        )

        kernel = np.ones(
            (3, 3),
            dtype=np.uint8,
        )

        green_mask = cv2.morphologyEx(
           green_mask,
           cv2.MORPH_CLOSE,
           kernel,
           iterations=2,
        )
        green_mask = cv2.morphologyEx(
            green_mask,
            cv2.MORPH_CLOSE,
            kernel,
        )

        if self.feather > 0:
            blur_size = (
                self.feather * 2 + 1
            )

            green_mask = cv2.GaussianBlur(
                green_mask,
                (blur_size, blur_size),
                0,
            )

        alpha_background = (
            green_mask.astype(np.float32)
            / 255.0
        )

        alpha_background = (
            alpha_background[..., None]
        )

        alpha_foreground = (
            1.0 - alpha_background
        )

        result = (
            foreground.astype(np.float32)
            * alpha_foreground
            + background.astype(np.float32)
            * alpha_background
        )

        result = np.clip(
            result,
            0,
            255,
        ).astype(np.uint8)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        success = cv2.imwrite(
            str(output_path),
            result,
        )

        if not success:
            raise BackgroundProcessingError(
                f"Unable to save processed image: {output_path}"
            )

        logger.info(
            "Virtual background created: photo=%s background=%s output=%s",
            photo_path,
            background_path,
            output_path,
        )

        return output_path

    @staticmethod
    def _cover_resize(
        image: np.ndarray,
        target_width: int,
        target_height: int,
    ) -> np.ndarray:
        """Resize and center-crop an image to fill the target size."""

        height, width = image.shape[:2]

        scale = max(
            target_width / width,
            target_height / height,
        )

        resized_width = int(
            round(width * scale)
        )

        resized_height = int(
            round(height * scale)
        )

        resized = cv2.resize(
            image,
            (
                resized_width,
                resized_height,
            ),
            interpolation=cv2.INTER_LANCZOS4,
        )

        x = max(
            0,
            (resized_width - target_width) // 2,
        )

        y = max(
            0,
            (resized_height - target_height) // 2,
        )

        return resized[
            y:y + target_height,
            x:x + target_width,
        ]
