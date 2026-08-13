from app.services.camera import CameraService


camera_service = CameraService(
    device="/dev/video0",
    width=1280,
    height=720,
    fps=30,
    jpeg_quality=80,
)
