from app.core.config import load_settings
from app.core.events import EventBus
from app.services.camera import CameraService
from app.services.collage import CollageGenerator
from app.services.photo_session import PhotoSessionService
from app.services.session_manager import SessionManager
from app.services.diagnostics import DiagnosticService
from pathlib import Path
from app.services.background import BackgroundProcessor
from app.services.printing import PrintService
from app.services.background_library import (
    BackgroundLibraryService,
)
from app.services.logo_library import (
    LogoLibraryService,
)

from app.services.settings_admin import (
    SettingsAdminService,
)

from app.services.greenscreen_calibration import (
    GreenscreenCalibrationService,
)

from app.services.test_print import (
    TestPrintService,
)

settings = load_settings()


camera_service = CameraService(
    device=settings.camera.device,
    width=settings.camera.width,
    height=settings.camera.height,
    fps=settings.camera.fps,
    jpeg_quality=settings.camera.jpeg_quality,
    retry_interval=settings.camera.retry_interval, 
)

greenscreen_calibration_service = (
    GreenscreenCalibrationService(
        camera_service=camera_service,
        calibration_directory=(
            settings.session.root.parent
            / "calibration"
        ),
    )
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

background_processor = BackgroundProcessor(
    hue_min=settings.background.greenscreen.hue_min,
    hue_max=settings.background.greenscreen.hue_max,
    saturation_min=(
        settings.background.greenscreen.saturation_min
    ),
    value_min=(
        settings.background.greenscreen.value_min
    ),
    feather=settings.background.greenscreen.feather,
)

background_library_service = (
    BackgroundLibraryService(
        background_directory=(
            settings.background.images[0].parent
        ),
    )
)

logo_library_service = LogoLibraryService(
    logo_directory=(
        settings.collage.logo.parent
        / "logos"
    ),
    active_logo_path=(
        settings.collage.logo
    ),
)

print_service = PrintService(
    printer_name=settings.printer.name,
    enabled=settings.printer.enabled,
)

test_print_service = TestPrintService(
    output_path=Path(
        "data/test-print.jpg"
    ),
    width=settings.collage.width,
    height=settings.collage.height,
    margin=settings.collage.margin,
)

photo_session_service = PhotoSessionService(
    session_manager=session_manager,
    camera_service=camera_service,
    collage_generator=collage_generator,
    background_processor=background_processor,
    print_service=print_service,
    event_bus=event_bus,
    session_root=settings.session.root,
    logo_path=settings.collage.logo,
    background_enabled=settings.background.enabled,
    background_images=settings.background.images,
    countdown_seconds=(
        settings.session.countdown_seconds
    ),
    photo_count=settings.session.photo_count,
    interval_seconds=(
        settings.session.interval_seconds
    ),
)
settings_admin_service = SettingsAdminService(
    photo_session_service=photo_session_service,
    background_processor=background_processor,
)

diagnostic_service = DiagnosticService(
    camera_service=camera_service,
    session_manager=session_manager,
    photo_session_service=photo_session_service,
    data_path=settings.session.root,
    log_path=Path("data/logs/fotobox.log"),
)

