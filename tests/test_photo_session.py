from pathlib import Path

import pytest
from PIL import Image

from app.core.events import EventBus
from app.models.state import (
    FotoboxState,
    SessionCommand,
)
from app.services.collage import CollageGenerator
from app.services.photo_session import (
    PhotoSessionService,
)
from app.services.session_manager import (
    SessionManager,
)
from app.services.background import BackgroundProcessor

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

        image = Image.new(
            "RGB",
            (1280, 720),
            "gray",
        )

        image.save(
            path,
            format="JPEG",
        )


@pytest.mark.asyncio
async def test_capture_and_collage_sequence(
    tmp_path: Path,
) -> None:
    manager = SessionManager()

    camera = FakeCamera()

    collage_generator = CollageGenerator(
        width=1800,
        height=1200,
    )

    service = PhotoSessionService(
        session_manager=manager,
        camera_service=camera,  # type: ignore[arg-type]
        collage_generator=collage_generator,
        background_processor=BackgroundProcessor(),
        event_bus=EventBus(),
        session_root=tmp_path,
        logo_path=(
            tmp_path / "missing-logo.png"    
        ),
        background_enabled=False,
        background_images=(),
        countdown_seconds=1,
        photo_count=3,
        interval_seconds=0,
    )

    manager.handle(
        SessionCommand.START_SESSION
    )

    manager.handle(
        SessionCommand.COUNTDOWN_FINISHED
    )

    await service._capture_photos()

    assert (
        manager.state
        == FotoboxState.PROCESSING
    )

    assert len(
        manager.session.photos
    ) == 3

    photo_paths = await service._prepare_photos()

    await service._create_collage(
        photo_paths
    )

    assert (
        manager.state
        == FotoboxState.PREVIEW
    )

    assert (
        manager.session.collage
        is not None
    )

    collage_path = Path(
        manager.session.collage
    )

    assert collage_path.exists()

    collage = Image.open(
        collage_path
    )

    assert collage.size == (
        1800,
        1200,
    )

