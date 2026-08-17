from app.core.config import load_settings
from app.core.events import EventBus
from app.services.camera import CameraService
from app.services.collage import CollageGenerator
from app.services.photo_session import PhotoSessionService
from app.services.session_manager import SessionManager
from app.services.diagnostics import DiagnosticService

settings = load_settings()


camera_service = CameraService(
    device=settings.camera.device,
    width=settings.camera.width,
    height=settings.camera.height,
    fps=settings.camera.fps,
    jpeg_quality=settings.camera.jpeg_quality,
    retry_interval=settings.camera.retry_interval, 
)


session_manager = SessionManager()

event_bus = EventBus()


collage_generator = CollageGenerator(
    width=settings.collage.width,
    height=settings.collage.height,
    gap=settings.collage.gap,
    margin=settings.collage.margin,
    jpeg_quality=settings.collage.jpeg_quality,
)


photo_session_service = PhotoSessionService(
    session_manager=session_manager,
    camera_service=camera_service,
    collage_generator=collage_generator,
    event_bus=event_bus,
    session_root=settings.session.root,
    logo_path=settings.collage.logo,
    countdown_seconds=(
        settings.session.countdown_seconds
    ),
    photo_count=settings.session.photo_count,
    interval_seconds=(
        settings.session.interval_seconds
    ),
)

diagnostic_service = DiagnosticService(
    camera_service=camera_service,
    session_manager=session_manager,
    photo_session_service=photo_session_service,
    data_path=settings.session.root,
)

