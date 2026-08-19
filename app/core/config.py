from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEFAULT_CONFIG_PATH = (
    BASE_DIR / "config" / "fotobox.yaml"
)


class ConfigurationError(Exception):
    """Raised when the Fotobox configuration is invalid."""


@dataclass(frozen=True)
class CameraSettings:
    device: str
    width: int
    height: int
    fps: int
    jpeg_quality: int
    retry_interval: float


@dataclass(frozen=True)
class SessionSettings:
    root: Path
    countdown_seconds: int
    photo_count: int
    interval_seconds: float


@dataclass(frozen=True)
class CollageSettings:
    width: int
    height: int
    margin: int
    gap: int
    jpeg_quality: int
    logo: Path


@dataclass(frozen=True)
class GreenscreenSettings:
    hue_min: int
    hue_max: int
    saturation_min: int
    value_min: int
    feather: int


@dataclass(frozen=True)
class BackgroundSettings:
    enabled: bool
    mode: str
    images: tuple[Path, ...]
    greenscreen: GreenscreenSettings


@dataclass(frozen=True)
class PrinterSettings:
    enabled: bool
    name: str


@dataclass(frozen=True)
class Settings:
    camera: CameraSettings
    session: SessionSettings
    collage: CollageSettings
    background: BackgroundSettings
    printer: PrinterSettings


def _project_path(value: str) -> Path:
    """Resolve a path relative to the project directory."""

    path = Path(value)

    if path.is_absolute():
        return path

    return BASE_DIR / path


def _section(
    data: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    """Return a required configuration section."""

    value = data.get(name)

    if not isinstance(value, dict):
        raise ConfigurationError(
            f"Missing or invalid configuration section: {name}"
        )

    return value


def load_settings(
    path: Path = DEFAULT_CONFIG_PATH,
) -> Settings:
    """Load and validate the Fotobox configuration."""

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw = yaml.safe_load(file)

    except OSError as exc:
        raise ConfigurationError(
            f"Unable to read configuration: {path}"
        ) from exc

    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Invalid YAML configuration: {path}"
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigurationError(
            "Configuration root must be a mapping."
        )

    try:
        camera = _section(
            raw,
            "camera",
        )

        session = _section(
            raw,
            "session",
        )

        collage = _section(
            raw,
            "collage",
        )

        background = _section(
            raw,
            "background",
        )

        greenscreen = _section(
            background,
            "greenscreen",
        )

        printer = _section(
            raw,
            "printer",
        )

        settings = Settings(
            camera=CameraSettings(
                device=str(
                    camera["device"]
                ),
                width=int(
                    camera["width"]
                ),
                height=int(
                    camera["height"]
                ),
                fps=int(
                    camera["fps"]
                ),
                jpeg_quality=int(
                    camera["jpeg_quality"]
                ),
                retry_interval=float(
                    camera["retry_interval"]
                ),
            ),

            session=SessionSettings(
                root=_project_path(
                    str(session["root"])
                ),
                countdown_seconds=int(
                    session["countdown_seconds"]
                ),
                photo_count=int(
                    session["photo_count"]
                ),
                interval_seconds=float(
                    session["interval_seconds"]
                ),
            ),

            collage=CollageSettings(
                width=int(
                    collage["width"]
                ),
                height=int(
                    collage["height"]
                ),
                margin=int(
                    collage["margin"]
                ),
                gap=int(
                    collage["gap"]
                ),
                jpeg_quality=int(
                    collage["jpeg_quality"]
                ),
                logo=_project_path(
                    str(collage["logo"])
                ),
            ),

            background=BackgroundSettings(
                enabled=bool(
                    background["enabled"]
                ),
                mode=str(
                    background["mode"]
                ),
                images=tuple(
                    _project_path(
                        str(image_path)
                    )
                    for image_path
                    in background["images"]
                ),
                greenscreen=GreenscreenSettings(
                    hue_min=int(
                        greenscreen["hue_min"]
                    ),
                    hue_max=int(
                        greenscreen["hue_max"]
                    ),
                    saturation_min=int(
                        greenscreen["saturation_min"]
                    ),
                    value_min=int(
                        greenscreen["value_min"]
                    ),
                    feather=int(
                        greenscreen["feather"]
                    ),
                ),
            ),

            printer=PrinterSettings(
                enabled=bool(
                    printer["enabled"]
                ),
                name=str(
                    printer["name"]
                ),
            ),
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise ConfigurationError(
            f"Invalid configuration value: {exc}"
        ) from exc

    _validate_settings(
        settings
    )

    return settings


def _validate_settings(
    settings: Settings,
) -> None:
    """Validate configuration values."""

    if settings.camera.width <= 0:
        raise ConfigurationError(
            "camera.width must be greater than zero."
        )

    if settings.camera.height <= 0:
        raise ConfigurationError(
            "camera.height must be greater than zero."
        )

    if settings.camera.fps <= 0:
        raise ConfigurationError(
            "camera.fps must be greater than zero."
        )

    if settings.camera.retry_interval <= 0:
        raise ConfigurationError(
            "camera.retry_interval must be greater than zero."
        )

    if not 1 <= settings.camera.jpeg_quality <= 100:
        raise ConfigurationError(
            "camera.jpeg_quality must be between 1 and 100."
        )

    if settings.session.countdown_seconds < 1:
        raise ConfigurationError(
            "session.countdown_seconds must be at least 1."
        )

    if settings.session.photo_count != 3:
        raise ConfigurationError(
            "The current 2x2 layout requires exactly 3 photos."
        )

    if settings.session.interval_seconds < 0:
        raise ConfigurationError(
            "session.interval_seconds must not be negative."
        )

    if settings.collage.width <= 0:
        raise ConfigurationError(
            "collage.width must be greater than zero."
        )

    if settings.collage.height <= 0:
        raise ConfigurationError(
            "collage.height must be greater than zero."
        )

    if settings.collage.margin < 0:
        raise ConfigurationError(
            "collage.margin must not be negative."
        )

    if settings.collage.gap < 0:
        raise ConfigurationError(
            "collage.gap must not be negative."
        )

    if not 1 <= settings.collage.jpeg_quality <= 100:
        raise ConfigurationError(
            "collage.jpeg_quality must be between 1 and 100."
        )

    if settings.background.mode != "greenscreen":
        raise ConfigurationError(
            "background.mode must currently be 'greenscreen'."
        )

    if settings.background.enabled:
        if len(settings.background.images) != 3:
            raise ConfigurationError(
                "Exactly three background images are required."
            )

    gs = settings.background.greenscreen

    if not 0 <= gs.hue_min <= 179:
        raise ConfigurationError(
            "background.greenscreen.hue_min "
            "must be between 0 and 179."
        )

    if not 0 <= gs.hue_max <= 179:
        raise ConfigurationError(
            "background.greenscreen.hue_max "
            "must be between 0 and 179."
        )

    if gs.hue_min >= gs.hue_max:
        raise ConfigurationError(
            "background.greenscreen.hue_min "
            "must be smaller than hue_max."
        )

    if not 0 <= gs.saturation_min <= 255:
        raise ConfigurationError(
            "background.greenscreen.saturation_min "
            "must be between 0 and 255."
        )

    if not 0 <= gs.value_min <= 255:
        raise ConfigurationError(
            "background.greenscreen.value_min "
            "must be between 0 and 255."
        )

    if gs.feather < 0:
        raise ConfigurationError(
            "background.greenscreen.feather "
            "must not be negative."
        )

    if not settings.printer.name.strip():
        raise ConfigurationError(
            "printer.name must not be empty."
        )
