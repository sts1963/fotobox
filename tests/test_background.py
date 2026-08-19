from pathlib import Path

import cv2
import numpy as np
import pytest

from app.services.background import (
    BackgroundProcessingError,
    BackgroundProcessor,
)


def test_replace_greenscreen(
    tmp_path: Path,
) -> None:
    foreground = np.zeros(
        (200, 300, 3),
        dtype=np.uint8,
    )

    foreground[:] = (
        0,
        255,
        0,
    )

    cv2.rectangle(
        foreground,
        (100, 50),
        (200, 180),
        (128, 128, 128),
        -1,
    )

    foreground_path = (
        tmp_path / "foreground.jpg"
    )

    cv2.imwrite(
        str(foreground_path),
        foreground,
    )

    background = np.zeros(
        (200, 300, 3),
        dtype=np.uint8,
    )

    background[:] = (
        255,
        0,
        0,
    )

    background_path = (
        tmp_path / "background.jpg"
    )

    cv2.imwrite(
        str(background_path),
        background,
    )

    output_path = (
        tmp_path / "result.jpg"
    )

    processor = BackgroundProcessor(
        hue_min=35,
        hue_max=90,
        saturation_min=60,
        value_min=40,
        feather=0,
    )

    result = processor.replace_greenscreen(
        photo_path=foreground_path,
        background_path=background_path,
        output_path=output_path,
    )

    assert result == output_path
    assert output_path.exists()

    image = cv2.imread(
        str(output_path)
    )

    assert image is not None

    assert image.shape[:2] == (
        200,
        300,
    )


def test_missing_foreground(
    tmp_path: Path,
) -> None:
    background_path = (
        tmp_path / "background.jpg"
    )

    background = np.zeros(
        (100, 100, 3),
        dtype=np.uint8,
    )

    cv2.imwrite(
        str(background_path),
        background,
    )

    processor = BackgroundProcessor()

    with pytest.raises(
        BackgroundProcessingError
    ):
        processor.replace_greenscreen(
            photo_path=(
                tmp_path / "missing.jpg"
            ),
            background_path=background_path,
            output_path=(
                tmp_path / "result.jpg"
            ),
        )


def test_missing_background(
    tmp_path: Path,
) -> None:
    photo_path = (
        tmp_path / "photo.jpg"
    )

    photo = np.zeros(
        (100, 100, 3),
        dtype=np.uint8,
    )

    cv2.imwrite(
        str(photo_path),
        photo,
    )

    processor = BackgroundProcessor()

    with pytest.raises(
        BackgroundProcessingError
    ):
        processor.replace_greenscreen(
            photo_path=photo_path,
            background_path=(
                tmp_path / "missing-background.jpg"
            ),
            output_path=(
                tmp_path / "result.jpg"
            ),
        )

