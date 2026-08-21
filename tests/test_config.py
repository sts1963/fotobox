from pathlib import Path

import pytest

from app.core.config import (
    ConfigurationError,
    load_settings,
)


def test_load_configuration(
    tmp_path: Path,
) -> None:
    config = tmp_path / "fotobox.yaml"

    config.write_text(
        """
camera:
  device: "/dev/video0"
  width: 1280
  height: 720
  fps: 30
  jpeg_quality: 80
  retry_interval: 2.0

session:
  root: "data/sessions"
  countdown_seconds: 5
  photo_count: 3
  interval_seconds: 5

collage:
  width: 1800
  height: 1200
  margin: 24
  gap: 24
  jpeg_quality: 95
  logo: "assets/logo.png"
background:
  enabled: false
  mode: "greenscreen"

  images:
    - "assets/backgrounds/background_01.jpg"
    - "assets/backgrounds/background_02.jpg"
    - "assets/backgrounds/background_03.jpg"

  greenscreen:
    hue_min: 35
    hue_max: 90
    saturation_min: 60
    value_min: 40
    feather: 5

printer:
  enabled: false
  name: "fotobox"
""",
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert settings.camera.device == "/dev/video0"
    assert settings.camera.width == 1280
    assert settings.camera.height == 720

    assert settings.session.photo_count == 3

    assert settings.collage.width == 1800
    assert settings.collage.height == 1200

    assert settings.printer.enabled is False
    assert settings.printer.name == "fotobox"


def test_invalid_photo_count(
    tmp_path: Path,
) -> None:
    config = tmp_path / "fotobox.yaml"

    config.write_text(
        """
camera:
  device: "/dev/video0"
  width: 1280
  height: 720
  fps: 30
  jpeg_quality: 80
  retry_interval: 2.0

  assert settings.camera.retry_interval == 2.0

session:
  root: "data/sessions"
  countdown_seconds: 5
  photo_count: 4
  interval_seconds: 5

collage:
  width: 1800
  height: 1200
  margin: 24
  gap: 24
  jpeg_quality: 95
  logo: "assets/logo.png"

printer:
  enabled: false
  name: "fotobox"
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError
    ):
        load_settings(config)

