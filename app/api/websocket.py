import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.state import SessionCommand
from app.services.countdown import CountdownService
from app.services.session_manager import (
    InvalidTransitionError,
    SessionManager,
)


router = APIRouter()

session_manager = SessionManager()


async def send_state(websocket: WebSocket) -> None:
    """Send the current session state to the client."""

    session = session_manager.session

    await websocket.send_json(
        {
            "type": "state",
            "state": session.state.value,
            "session_id": session.id,
            "photos": session.photos,
            "collage": session.collage,
            "error": session.error,
            "countdown": session.countdown_remaining,
        }
    )


async def countdown_tick(
    websocket: WebSocket,
    remaining: int,
) -> None:
    """Handle a countdown tick."""

    session_manager.set_countdown(remaining)

    try:
        await send_state(websocket)
    except Exception:
        # The client may have disconnected.
        pass


async def countdown_finished(
    websocket: WebSocket,
) -> None:
    """Handle completion of the countdown."""

    session_manager.handle(
        SessionCommand.COUNTDOWN_FINISHED
    )

    try:
        await send_state(websocket)
    except Exception:
        pass


async def run_countdown(websocket: WebSocket) -> None:
    """Run the session countdown."""

    countdown = CountdownService(
        seconds=5,
        on_tick=lambda remaining: countdown_tick(
            websocket,
            remaining,
        ),
        on_finished=lambda: countdown_finished(
            websocket,
        ),
    )

    try:
        await countdown.start()

        # Keep the task alive until the countdown has finished.
        while countdown.running:
            await asyncio.sleep(0.05)

    except asyncio.CancelledError:
        await countdown.cancel()
        raise


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle the frontend WebSocket connection."""

    await websocket.accept()

    await send_state(websocket)

    countdown_task: asyncio.Task[None] | None = None

    try:
        while True:
            message = await websocket.receive_json()

            command_name = message.get("type")

            try:
                command = SessionCommand(command_name)

            except ValueError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Unknown command: {command_name}",
                    }
                )
                continue

            try:
                new_state = session_manager.handle(command)

            except InvalidTransitionError as exc:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(exc),
                    }
                )
                continue

            await send_state(websocket)

            if new_state.value == "countdown":
                if countdown_task is None or countdown_task.done():
                    countdown_task = asyncio.create_task(
                        run_countdown(websocket)
                    )

    except WebSocketDisconnect:
        if countdown_task is not None:
            countdown_task.cancel()

            try:
                await countdown_task
            except asyncio.CancelledError:
                pass
