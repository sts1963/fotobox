from pathlib import Path

import pytest

from app.core.events import EventBus
from app.models.state import FotoboxState
from app.services.photo_session import (
    PhotoSessionService,
)
from app.services.session_manager import (
    SessionManager,
)


class FakeCamera:
    """Minimal camera double for session tests."""

    available = True

    def capture_photo(
        self,
        path: Path,
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_bytes(
            b"fake-image-data"
        )


@pytest.mark.asyncio
async def test_capture_sequence(
    tmp_path: Path,
) -> None:
    manager = SessionManager()

    camera = FakeCamera()

    service = PhotoSessionService(
        session_manager=manager,
        camera_service=camera,  # type: ignore[arg-type]
        event_bus=EventBus(),
        session_root=tmp_path,
        countdown_seconds=1,
        photo_count=3,
        interval_seconds=0,
    )

    # Put the state machine directly into CAPTURING.
    from app.models.state import SessionCommand

    manager.handle(
        SessionCommand.START_SESSION
    )

    manager.handle(
        SessionCommand.COUNTDOWN_FINISHED
    )

    await service._capture_photos()

    assert manager.state == FotoboxState.PROCESSING
    assert len(manager.session.photos) == 3

    for filename in manager.session.photos:
        assert Path(filename).exists()

