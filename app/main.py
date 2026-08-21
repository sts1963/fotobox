from pathlib import Path
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.routes import router as api_router
from app.api.websocket import router as websocket_router
from app.core.logging_config import configure_logging
from app.services.container import camera_service


BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = (
    BASE_DIR
    / "frontend"
)

BACKGROUND_DIR = (
    BASE_DIR
    / "assets"
    / "backgrounds"
)

LOGO_LIBRARY_DIR = (
    BASE_DIR
    / "assets"
    / "logos"
)

LOG_FILE = (
    BASE_DIR
    / "data"
    / "logs"
    / "fotobox.log"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    configure_logging(
        LOG_FILE
    )

    logger = logging.getLogger(
        __name__
    )

    logger.info(
        "Fotobox application starting"
    )

    try:
        camera_service.start()

        logger.info(
            "Camera service management started"
        )

    except Exception:
        logger.exception(
            "Camera service failed during startup"
        )

    yield

    logger.info(
        "Fotobox application shutting down"
    )

    camera_service.stop()

    logger.info(
        "Camera service stopped"
    )


app = FastAPI(
    title="Fotobox",
    version="0.1.0",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)

app.mount(
    "/background-assets",
    StaticFiles(
        directory=BACKGROUND_DIR
    ),
    name="background-assets",
)

app.mount(
    "/logo-assets",
    StaticFiles(
        directory=LOGO_LIBRARY_DIR
    ),
    name="logo-assets",
)


app.include_router(
    api_router
)

app.include_router(
    websocket_router
)

app.include_router(
    admin_router
)


@app.get(
    "/",
    include_in_schema=False,
)
async def index() -> FileResponse:
    """Serve the frontend application."""

    return FileResponse(
        FRONTEND_DIR / "index.html",
        headers={
            "Cache-Control": "no-store",
        },
    )

@app.get(
    "/console",
    include_in_schema=False,
)
async def console() -> FileResponse:
    """Serve the local Fotobox service console."""

    return FileResponse(
        FRONTEND_DIR
        / "console.html"
    )


@app.get(
    "/backgrounds",
    include_in_schema=False,
)
async def backgrounds() -> FileResponse:
    """Serve the virtual background administration."""

    return FileResponse(
        FRONTEND_DIR
        / "backgrounds.html"
    )

@app.get(
    "/settings",
    include_in_schema=False,
)
async def settings_page() -> FileResponse:
    """Serve the Fotobox settings administration."""

    return FileResponse(
        FRONTEND_DIR / "settings.html"
    )

@app.get(
    "/active-logo",
    include_in_schema=False,
)
async def active_logo() -> FileResponse:
    """Serve the currently active logo."""

    logo_path = (
        BASE_DIR
        / "assets"
        / "logo.png"
    )

    if not logo_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="No active logo configured.",
        )

    return FileResponse(
        logo_path
    )
