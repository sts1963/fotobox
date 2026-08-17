from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.api.websocket import router as websocket_router

from app.services.container import camera_service 

import logging
from app.core.logging_config import configure_logging

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
LOG_FILE = BASE_DIR / "data" / "logs" / "fotobox.log"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    configure_logging(LOG_FILE)
    logger = logging.getLogger(__name__)

    logger.info("Fotobox application starting")

    try:
        camera_service.start()
        logger.info("Camera service management started")
    except Exception:
        logger.exception(
            "Camera service failed during startup"
        )

    yield

    logger.info("Fotobox application shutting down")

    camera_service.stop()

    logger.info("Camera service stopped")

app = FastAPI(
    title="Fotobox",
    version="0.1.0",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)

app.include_router(api_router)
app.include_router(websocket_router)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve the frontend application."""

    return FileResponse(FRONTEND_DIR / "index.html")
