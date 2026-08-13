from pathlib import Path
from typing import Any

import yaml


class Config:
    """Loads and provides access to the Fotobox configuration."""

    def __init__(self, filename: str = "config/fotobox.yaml") -> None:
        self.filename = Path(filename)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.filename.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.filename}"
            )

        with self.filename.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ValueError("Configuration must contain a YAML mapping.")

        return data

    def get(self, *keys: str, default: Any = None) -> Any:
        """Return a nested configuration value."""

        value: Any = self.data

        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default

            value = value[key]

        return value

    @property
    def server_host(self) -> str:
        return str(
            self.get(
                "server",
                "host",
                default="0.0.0.0",
            )
        )

    @property
    def server_port(self) -> int:
        return int(
            self.get(
                "server",
                "port",
                default=8000,
            )
        )

    @property
    def session_directory(self) -> Path:
        return Path(
            self.get(
                "storage",
                "session_directory",
                default="data/sessions",
            )
        )
