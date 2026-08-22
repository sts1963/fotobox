from __future__ import annotations

import io
import shutil
import zipfile

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class SessionArchiveError(Exception):
    """Raised when session archive operations fail."""


@dataclass(frozen=True)
class SessionArchiveInfo:
    session_id: str
    created_at: datetime
    photo_count: int
    has_collage: bool
    size_bytes: int
    collage_path: Path | None


class SessionArchiveService:
    """Inspect, export and later clean stored photo sessions."""

    def __init__(
        self,
        session_root: Path,
    ) -> None:
        self.session_root = session_root

    def delete_all_except(
        self,
        protected_session_id: str | None = None,
    ) -> int:
        """Delete all stored sessions except the protected one."""

        deleted_count = 0

        for session in self.list_sessions():
            if (
                protected_session_id is not None
                and session.session_id
                == protected_session_id
            ):
                continue

            try:
                self.delete_session(
                    session.session_id,
                    protected_session_id=(
                        protected_session_id
                    ),
                )
            except SessionArchiveError:
                continue

            deleted_count += 1

        return deleted_count

    def list_sessions(
        self,
    ) -> list[SessionArchiveInfo]:
        """Return all stored sessions, newest first."""

        if not self.session_root.exists():
            return []

        sessions: list[SessionArchiveInfo] = []

        for directory in self.session_root.iterdir():
            if not directory.is_dir():
                continue

            try:
                sessions.append(
                    self._inspect_session(
                        directory
                    )
                )
            except OSError:
                continue

        sessions.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )

        return sessions

    def get_summary(
        self,
    ) -> dict:
        """Return statistics about stored sessions."""

        sessions = self.list_sessions()

        collage_count = sum(
            1
            for session in sessions
            if session.has_collage
        )

        total_size = sum(
            session.size_bytes
            for session in sessions
        )

        return {
            "session_count": len(sessions),
            "collage_count": collage_count,
            "size_bytes": total_size,
            "size_mb": round(
                total_size / 1024 / 1024,
                1,
            ),
            "oldest": (
                sessions[-1].created_at.isoformat()
                if sessions
                else None
            ),
            "newest": (
                sessions[0].created_at.isoformat()
                if sessions
                else None
            ),
        }

    def create_collage_archive(
        self,
    ) -> bytes:
        """Create a ZIP containing all finished collages."""

        sessions = [
            session
            for session in reversed(
                self.list_sessions()
            )
            if session.has_collage
            and session.collage_path is not None
        ]

        if not sessions:
            raise SessionArchiveError(
                "No collages are available."
            )

        buffer = io.BytesIO()

        with zipfile.ZipFile(
            buffer,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for number, session in enumerate(
                sessions,
                start=1,
            ):
                filename = (
                    f"collage-{number:04d}.jpg"
                )

                archive.write(
                    session.collage_path,
                    arcname=filename,
                )

        return buffer.getvalue()

    def _inspect_session(
        self,
        directory: Path,
    ) -> SessionArchiveInfo:
        """Inspect one session directory."""

        files = [
            path
            for path in directory.iterdir()
            if path.is_file()
        ]

        size_bytes = sum(
            path.stat().st_size
            for path in files
        )

        photos = list(
            directory.glob(
                "photo_*.jpg"
            )
        )

        collage_path = (
            directory / "collage.jpg"
        )

        if not collage_path.exists():
            collage_path = None

        created_at = datetime.fromtimestamp(
            directory.stat().st_mtime
        )

        return SessionArchiveInfo(
            session_id=directory.name,
            created_at=created_at,
            photo_count=len(photos),
            has_collage=(
                collage_path is not None
            ),
            size_bytes=size_bytes,
            collage_path=collage_path,
        )

    def get_collage_path(
        self,
        session_id: str,
    ) -> Path:
        """Return the collage path for one stored session."""

        session_directory = (
            self.session_root
            / session_id
        )

        if not session_directory.is_dir():
            raise SessionArchiveError(
                "Session not found."
            )

        collage_path = (
            session_directory
            / "collage.jpg"
        )

        if not collage_path.is_file():
            raise SessionArchiveError(
                "Collage not found."
            )

        return collage_path


    def delete_session(
        self,
        session_id: str,
        *,
        protected_session_id: str | None = None,
    ) -> None:
        """Delete one stored session directory."""

        if (
            protected_session_id is not None
            and session_id
            == protected_session_id
        ):
            raise SessionArchiveError(
                "The active session cannot be deleted."
            )

        session_directory = (
            self.session_root
            / session_id
        )

        if not session_directory.is_dir():
            raise SessionArchiveError(
                "Session not found."
            )

        #
        # Do not allow path traversal via a manipulated
        # session ID.
        #
        root = self.session_root.resolve()
        target = session_directory.resolve()

        if root not in target.parents:
            raise SessionArchiveError(
                "Invalid session path."
            )

        try:
            shutil.rmtree(
                target
            )
        except OSError as exc:
            raise SessionArchiveError(
                "Unable to delete session."
            ) from exc
