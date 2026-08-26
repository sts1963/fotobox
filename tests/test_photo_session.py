from pathlib import Path
from PIL import Image

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

from app.services.background_library import (
    BackgroundLibraryService,
)

class FakePrintService:
    """Minimal print service for photo session tests."""

    def print_collage(
        self,
        collage_path: Path,
    ) -> str:
        return "test-job"

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
    background_library_service = (
        BackgroundLibraryService(
            background_directory=(
                tmp_path / "backgrounds"
            ),
        )
    )
    service = PhotoSessionService(
        session_manager=manager,
        camera_service=camera,  # type: ignore[arg-type]
        collage_generator=collage_generator,
        background_processor=BackgroundProcessor(),
        background_library_service=(
            background_library_service
        ),
        print_service=FakePrintService(),  # type: ignore[arg-type]
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

def test_random_background_selection(
    tmp_path: Path,
) -> None:
    background_directory = (
        tmp_path / "backgrounds"
    )

    library_service = (
        BackgroundLibraryService(
            background_directory=(
                background_directory
            ),
        )
    )

    for index in range(1, 4):
        image_path = (
            library_service.library_directory
            / f"background-{index}.jpg"
        )

        image = Image.new(
            "RGB",
            (100, 100),
            (
                index * 40,
                index * 40,
                index * 40,
            ),
        )

        image.save(
            image_path,
            format="JPEG",
        )

    service = PhotoSessionService(
        session_manager=SessionManager(),
        camera_service=FakeCamera(),  # type: ignore[arg-type]
        collage_generator=CollageGenerator(),
        background_processor=BackgroundProcessor(),
        background_library_service=(
            library_service
        ),
        print_service=FakePrintService(),  # type: ignore[arg-type]
        event_bus=EventBus(),
        session_root=tmp_path,
        background_enabled=True,
        background_selection_mode="random",
        background_images=(),
    )

    selected = service._select_backgrounds(
        3
    )

    assert len(selected) == 3
    assert len(set(selected)) == 3

    assert all(
        path.parent
        == library_service.library_directory
        for path in selected
    )
