from pathlib import Path

from app.services.camera import CameraService
from app.services.diagnostics import DiagnosticService
from app.services.photo_session import PhotoSessionService
from app.services.session_manager import SessionManager
from app.services.collage import CollageGenerator
from app.core.events import EventBus
from app.services.background import BackgroundProcessor

def test_diagnostic_snapshot(
    tmp_path: Path,
) -> None:
    camera = CameraService()

    session_manager = SessionManager()

    photo_session_service = PhotoSessionService(
         session_manager=session_manager,
         camera_service=camera,
         collage_generator=CollageGenerator(),
         background_processor=BackgroundProcessor(),
         event_bus=EventBus(),
         session_root=tmp_path,
         background_enabled=False,
         background_images=(),
    )

    diagnostics = DiagnosticService(
        camera_service=camera,
        session_manager=session_manager,
        photo_session_service=photo_session_service,
        data_path=tmp_path,
        log_path=tmp_path / "fotobox.log",
    )

    result = diagnostics.snapshot()

    assert result["application"]["status"] == "running"

    assert result["camera"]["state"] == "stopped"
    assert result["camera"]["available"] is False

    assert result["session"]["state"] == "start"
    assert result["session"]["running"] is False

    assert "disk" in result["system"]

def test_diagnostic_log_lines(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "fotobox.log"

    log_path.write_text(
        "line 1\n"
        "line 2\n"
        "line 3\n"
        "line 4\n",
        encoding="utf-8",
    )

    camera = CameraService()
    session_manager = SessionManager()

    photo_session_service = PhotoSessionService(
        session_manager=session_manager,
        camera_service=camera,
        collage_generator=CollageGenerator(),
        background_processor=BackgroundProcessor(),
        event_bus=EventBus(),
        session_root=tmp_path,
        background_enabled=False,
        background_images=(),
    )

    diagnostics = DiagnosticService(
        camera_service=camera,
        session_manager=session_manager,
        photo_session_service=photo_session_service,
        data_path=tmp_path,
        log_path=log_path,
    )

    lines = diagnostics.get_log_lines(
        limit=2
    )

    assert lines == [
        "line 3",
        "line 4",
    ]

