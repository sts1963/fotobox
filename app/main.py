from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.api.websocket import router as websocket_router

from app.services.container import camera_service 

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    try:
        camera_service.start()
    except Exception as exc:
        print(f"Camera startup failed: {exc}")

    yield

    camera_service.stop()

app = FastAPI(
    title="Fotobox",
    version="0.1.0",
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
