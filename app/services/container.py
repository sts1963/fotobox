from pathlib import Path

from app.core.events import EventBus
from app.services.camera import CameraService
from app.services.collage import CollageGenerator
from app.services.photo_session import PhotoSessionService
from app.services.session_manager import SessionManager


camera_service = CameraService(
    device="/dev/video0",
    width=1280,
    height=720,
    fps=30,
    jpeg_quality=80,
)


session_manager = SessionManager()

event_bus = EventBus()


collage_generator = CollageGenerator(
    width=1800,
    height=1200,
    gap=24,
    margin=24,
)


photo_session_service = PhotoSessionService(
    session_manager=session_manager,
    camera_service=camera_service,
    collage_generator=collage_generator,
    event_bus=event_bus,
    session_root=Path("data/sessions"),
    logo_path=Path("assets/logo.png"),
    countdown_seconds=5,
    photo_count=3,
    interval_seconds=3,
)

