from pathlib import Path

from app.services.camera import CameraService
from app.services.diagnostics import DiagnosticService
from app.services.photo_session import PhotoSessionService
from app.services.session_manager import SessionManager
from app.services.collage import CollageGenerator
from app.core.events import EventBus


def test_diagnostic_snapshot(
    tmp_path: Path,
) -> None:
    camera = CameraService()

    session_manager = SessionManager()

    photo_session_service = PhotoSessionService(
        session_manager=session_manager,
        camera_service=camera,
        collage_generator=CollageGenerator(),
        event_bus=EventBus(),
        session_root=tmp_path,
    )

    diagnostics = DiagnosticService(
        camera_service=camera,
        session_manager=session_manager,
        photo_session_service=photo_session_service,
        data_path=tmp_path,
    )

    result = diagnostics.snapshot()

    assert result["application"]["status"] == "running"

    assert result["camera"]["state"] == "stopped"
    assert result["camera"]["available"] is False

    assert result["session"]["state"] == "start"
    assert result["session"]["running"] is False

    assert "disk" in result["system"]

