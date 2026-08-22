from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

from app.services.camera import (
    CameraError,
    CameraService,
)


logger = logging.getLogger(__name__)


class GreenscreenCalibrationError(Exception):
    """Raised when greenscreen calibration fails."""


class GreenscreenCalibrationService:
    """Capture and analyse an empty greenscreen image."""

    def __init__(
        self,
        camera_service: CameraService,
        calibration_directory: Path,
    ) -> None:
        self.camera_service = camera_service
        self.calibration_directory = (
            calibration_directory
        )

        self.calibration_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def calibrate(self) -> dict:
        """Capture a reference image and suggest HSV values."""

        if not self.camera_service.available:
            raise GreenscreenCalibrationError(
                "Camera is not available."
            )

        photo_path = (
            self.calibration_directory
            / "greenscreen_reference.jpg"
        )

        try:
            self.camera_service.capture_photo(
                photo_path
            )
        except CameraError as exc:
            raise GreenscreenCalibrationError(
                "Unable to capture calibration image."
            ) from exc

        image = cv2.imread(
            str(photo_path)
        )

        if image is None:
            raise GreenscreenCalibrationError(
                "Unable to read calibration image."
            )

        suggestion = self._analyse(
            image
        )

        suggestion["reference_image"] = str(
            photo_path
        )

        logger.info(
            "Greenscreen calibration completed: %s",
            suggestion,
        )

        return suggestion

    def _analyse(
        self,
        image: np.ndarray,
    ) -> dict:
        """Analyse the dominant green colour of a greenscreen."""

        height, width = image.shape[:2]

        #
        # Ignore the outer 10 percent.
        #
        x1 = int(
            width * 0.10
        )
        x2 = int(
            width * 0.90
        )

        y1 = int(
            height * 0.10
        )
        y2 = int(
            height * 0.90
        )

        sample = image[
            y1:y2,
            x1:x2,
        ]

        if sample.size == 0:
            raise GreenscreenCalibrationError(
                "Calibration image contains no usable area."
            )

        hsv = cv2.cvtColor(
            sample,
            cv2.COLOR_BGR2HSV,
        )

        hue = hsv[:, :, 0]
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]

        #
        # First remove pixels which contain too little
        # colour information.
        #
        colour_valid = (
            (saturation >= 15)
            & (value >= 5)
        )

        #
        # For calibration we explicitly search for green.
        #
        # OpenCV hue:
        #   0 ... 179
        #
        # A deliberately wide green range is used here.
        #
        green_candidate = (
            colour_valid
            & (hue >= 20)
            & (hue <= 110)
        )

        candidate_count = int(
            np.count_nonzero(
                green_candidate
            )
        )

        total_count = int(
            hue.size
        )

        if (
            total_count == 0
            or candidate_count
            < total_count * 0.03
        ):
            raise GreenscreenCalibrationError(
                "Not enough green area was detected. "
                "Make sure the greenscreen fills most "
                "of the camera image."
            )

        #
        # Find the dominant green hue.
        #
        green_hues = hue[
            green_candidate
        ]

        histogram = np.bincount(
            green_hues.ravel(),
            minlength=180,
        )

        #
        # Do not allow a peak outside the green search
        # range even if noise happens to occur there.
        #
        histogram[:20] = 0
        histogram[111:] = 0

        dominant_hue = int(
            np.argmax(
                histogram
            )
        )

        #
        # Only use pixels reasonably close to the
        # dominant greenscreen colour.
        #
        hue_distance = 20

        screen_pixels = (
            (saturation >= 15)
            & (value >= 5)
            & (
                hue
                >= max(
                    0,
                    dominant_hue
                    - hue_distance,
               )
            )
            & (
                hue
                <= min(
                179,
                dominant_hue
                + hue_distance,
                )
            )
       )

        usable_count = int(
            np.count_nonzero(
                screen_pixels
            )
        )

        if usable_count < total_count * 0.05:
            raise GreenscreenCalibrationError(
                "Too few pixels match the dominant "
                "greenscreen colour."
            )

        valid_hue = hue[
            screen_pixels
        ].astype(
            np.float32
        )

        valid_saturation = saturation[
            screen_pixels
        ].astype(
            np.float32
        )

        valid_value = value[
            screen_pixels
        ].astype(
            np.float32
        )

        #
        # Ignore isolated extremes.
        #
        hue_low = float(
            np.percentile(
                valid_hue,
                2,
            )
        )

        hue_high = float(
            np.percentile(
                valid_hue,
                98,
            )
        )

        saturation_low = float(
            np.percentile(
                valid_saturation,
                2,
            )
        )

        value_low = float(
            np.percentile(
                valid_value,
                2,
            )
        )

        #
        # Add some tolerance for folds, shadows and
        # illumination differences.
        #
        hue_min = max(
            0,
            int(
                np.floor(
                    hue_low
                )
            )
            - 5,
        )

        hue_max = min(
            179,
            int(
                np.ceil(
                    hue_high
                )
            )
            + 5,
        )

        saturation_min = max(
            10,
            int(
                np.floor(
                    saturation_low
                )
            )
            - 5,
        )

        value_min = max(
            0,
            int(
                np.floor(
                    value_low
                )
            )
            - 5,
        )

        return {
            "hue_min": hue_min,
            "hue_max": hue_max,
            "saturation_min": saturation_min,
            "value_min": value_min,
            "feather": 3,

            "dominant_hue": dominant_hue,

            "sample_pixels": total_count,
            "usable_pixels": usable_count,

            "usable_ratio": round(
                usable_count
                / total_count,
                3,
            ),

            "measured": {
                "hue_low": round(
                    hue_low,
                    1,
                ),
                "hue_high": round(
                    hue_high,
                    1,
                ),
                "saturation_low": round(
                    saturation_low,
                    1,
                ),
                "value_low": round(
                    value_low,
                    1,
                ),
            },
        }

    def create_mask(
        self,
        *,
        hue_min: int,
        hue_max: int,
        saturation_min: int,
        value_min: int,
        use_test_image: bool = False,
    ) -> Path:
        """Create a preview mask using supplied HSV values."""

        if use_test_image:
            source_path = (
                self.calibration_directory
                / "greenscreen_test.jpg"
            )

            mask_path = (
                self.calibration_directory
                / "greenscreen_test_mask.png"
            )

        else:
            source_path = (
                self.calibration_directory
                / "greenscreen_reference.jpg"
            )

            mask_path = (
                self.calibration_directory
                / "greenscreen_mask.png"
            )

        if not source_path.is_file():
            raise GreenscreenCalibrationError(
                "Calibration image is not available."
            )

        image = cv2.imread(
            str(source_path)
        )

        if image is None:
            raise GreenscreenCalibrationError(
                "Unable to read calibration image."
            )

        hsv = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2HSV,
        )

        lower = np.array(
            [
                hue_min,
                saturation_min,
                value_min,
            ],
            dtype=np.uint8,
        )

        upper = np.array(
            [
                hue_max,
                255,
                255,
            ],
            dtype=np.uint8,
        )

        mask = cv2.inRange(
            hsv,
            lower,
            upper,
        )

        success = cv2.imwrite(
            str(mask_path),
            mask,
        )

        if not success:
            raise GreenscreenCalibrationError(
                "Unable to save calibration mask."
            )

        logger.info(
            "Greenscreen preview mask created: %s",
            mask_path,
        )

        return mask_path

    def capture_test_photo(
        self,
    ) -> Path:
        """Capture a person in front of the greenscreen."""

        if not self.camera_service.available:
            raise GreenscreenCalibrationError(
                "Camera is not available."
            )

        test_path = (
            self.calibration_directory
            / "greenscreen_test.jpg"
        )

        try:
            self.camera_service.capture_photo(
                test_path
            )

        except CameraError as exc:
            raise GreenscreenCalibrationError(
                "Unable to capture test image."
            ) from exc

        logger.info(
            "Greenscreen test image captured: %s",
            test_path,
        )

        return test_path
