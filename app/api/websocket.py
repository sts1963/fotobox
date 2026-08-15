from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.services.container import (
    event_bus,
    photo_session_service,
    session_manager,
)
from app.services.photo_session import (
    PhotoSessionBusyError,
)


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
) -> None:
    """Handle one frontend WebSocket connection."""

    await websocket.accept()

    async def send_event(
        event: dict,
    ) -> None:
        await websocket.send_json(event)

    event_bus.subscribe(send_event)

    try:
        # Synchronize a newly connected/reloaded frontend.
        await websocket.send_json(
            session_manager.snapshot()
        )

        while True:
            message = await websocket.receive_json()

            command = message.get("type")

            if command == "start_session":
                try:
                    await photo_session_service.start()

                except PhotoSessionBusyError as exc:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": str(exc),
                        }
                    )

            elif command == "restart":
                await photo_session_service.restart()

            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": (
                            f"Unknown command: {command}"
                        ),
                    }
                )

    except WebSocketDisconnect:
        pass

    finally:
        event_bus.unsubscribe(send_event)


