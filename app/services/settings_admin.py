from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from app.core.config import (
    DEFAULT_CONFIG_PATH,
    load_settings,
)
from app.services.background import BackgroundProcessor
from app.services.photo_session import PhotoSessionService


logger = logging.getLogger(__name__)


class SettingsAdminError(Exception):
    """Raised when administrative settings cannot be saved."""


class SettingsAdminService:
    """Read, validate, persist and apply Fotobox settings."""

    def __init__(
        self,
        photo_session_service: PhotoSessionService,
        background_processor: BackgroundProcessor,
        config_path: Path = DEFAULT_CONFIG_PATH,
    ) -> None:
        self.photo_session_service = (
            photo_session_service
        )

        self.background_processor = (
            background_processor
        )

        self.config_path = config_path

    def snapshot(
        self,
    ) -> dict[str, Any]:
        """Return the settings editable in the admin UI."""

        settings = load_settings(
            self.config_path
        )

        return {
            "session": {
                "countdown_seconds": (
                    settings.session.countdown_seconds
                ),
                "interval_seconds": (
                    settings.session.interval_seconds
                ),
            },
            "background": {
                "enabled": (
                    self.photo_session_service
                    .backgrounds_enabled
                ),
                "selection_mode": (
                    self.photo_session_service
                    .background_selection
                ),
                "greenscreen": {
                    "hue_min": (
                        self.background_processor
                        .hue_min
                    ),
                    "hue_max": (
                        self.background_processor
                        .hue_max
                    ),
                    "saturation_min": (
                        self.background_processor
                        .saturation_min
                    ),
                    "value_min": (
                        self.background_processor
                        .value_min
                    ),
                    "feather": (
                        self.background_processor
                        .feather
                    ),
                },
            },
        }

    def update_background_mode(
        self,
        *,
        enabled: bool,
        selection_mode: str,
    ) -> dict[str, Any]:
        """Persist and immediately apply background mode settings."""

        if selection_mode not in (
            "fixed",
            "random",
        ):
            raise SettingsAdminError(
                "Background selection mode must be "
                "'fixed' or 'random'."
            )

        raw = self._read_raw_config()

        background = raw.get(
            "background"
        )

        if not isinstance(
            background,
            dict,
        ):
            raise SettingsAdminError(
                "Invalid background configuration."
            )

        background[
            "enabled"
        ] = enabled

        background[
            "selection_mode"
        ] = selection_mode

        self._validate_and_replace(
            raw
        )

        self.photo_session_service.set_backgrounds_enabled(
            enabled
        )

        self.photo_session_service.set_background_selection_mode(
            selection_mode
        )

        logger.info(
            "Background mode settings updated: "
            "enabled=%s selection_mode=%s",
            enabled,
            selection_mode,
        )

        return {
            "enabled": (
                self.photo_session_service
                .backgrounds_enabled
            ),
            "selection_mode": (
                self.photo_session_service
                .background_selection
            ),
        }

    def update(
        self,
        *,
        countdown_seconds: int,
        interval_seconds: float,
        background_enabled: bool,
        hue_min: int,
        hue_max: int,
        saturation_min: int,
        value_min: int,
        feather: int,
    ) -> dict[str, Any]:
        """Validate, save and immediately apply settings."""

        raw = self._read_raw_config()

        session = raw.get(
            "session"
        )

        background = raw.get(
            "background"
        )

        if not isinstance(
            session,
            dict,
        ):
            raise SettingsAdminError(
                "Invalid session configuration."
            )

        if not isinstance(
            background,
            dict,
        ):
            raise SettingsAdminError(
                "Invalid background configuration."
            )

        greenscreen = background.get(
            "greenscreen"
        )

        if not isinstance(
            greenscreen,
            dict,
        ):
            raise SettingsAdminError(
                "Invalid greenscreen configuration."
            )

        session[
            "countdown_seconds"
        ] = countdown_seconds

        session[
            "interval_seconds"
        ] = interval_seconds

        background[
            "enabled"
        ] = background_enabled

        greenscreen[
            "hue_min"
        ] = hue_min

        greenscreen[
            "hue_max"
        ] = hue_max

        greenscreen[
            "saturation_min"
        ] = saturation_min

        greenscreen[
            "value_min"
        ] = value_min

        greenscreen[
            "feather"
        ] = feather

        self._validate_and_replace(
            raw
        )

        #
        # Apply the values to the already running services.
        #
        self.photo_session_service.countdown_seconds = (
            countdown_seconds
        )

        self.photo_session_service.interval_seconds = (
            interval_seconds
        )

        self.photo_session_service.set_backgrounds_enabled(
            background_enabled
        )

        self.background_processor.hue_min = (
            hue_min
        )

        self.background_processor.hue_max = (
            hue_max
        )

        self.background_processor.saturation_min = (
            saturation_min
        )

        self.background_processor.value_min = (
            value_min
        )

        self.background_processor.feather = (
            feather
        )

        logger.info(
            "Fotobox settings updated"
        )

        return self.snapshot()

    def _read_raw_config(
        self,
    ) -> dict[str, Any]:
        """Read the current YAML configuration."""

        try:
            with self.config_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                raw = yaml.safe_load(
                    file
                )

        except OSError as exc:
            raise SettingsAdminError(
                "Unable to read Fotobox configuration."
            ) from exc

        except yaml.YAMLError as exc:
            raise SettingsAdminError(
                "Fotobox configuration is invalid YAML."
            ) from exc

        if not isinstance(
            raw,
            dict,
        ):
            raise SettingsAdminError(
                "Fotobox configuration root is invalid."
            )

        return raw

    def _validate_and_replace(
        self,
        raw: dict[str, Any],
    ) -> None:
        """Write and validate a temporary config before replacing."""

        self.config_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.config_path.parent,
                prefix=".fotobox-",
                suffix=".yaml",
                delete=False,
            ) as temporary:
                temporary_path = Path(
                    temporary.name
                )

                yaml.safe_dump(
                    raw,
                    temporary,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                )

            #
            # This is the important safety check:
            # use exactly the same loader and validation
            # as application startup.
            #
            load_settings(
                temporary_path
            )

            os.replace(
                temporary_path,
                self.config_path,
            )

            temporary_path = None

        except Exception as exc:
            raise SettingsAdminError(
                f"Settings were not saved: {exc}"
            ) from exc

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()
