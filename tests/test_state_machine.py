import pytest

from app.models.state import FotoboxState, SessionCommand
from app.services.session_manager import (
    InvalidTransitionError,
    SessionManager,
)


def test_initial_state() -> None:
    manager = SessionManager()

    assert manager.state == FotoboxState.START


def test_start_session() -> None:
    manager = SessionManager()

    state = manager.handle(SessionCommand.START_SESSION)

    assert state == FotoboxState.COUNTDOWN


def test_complete_capture_flow() -> None:
    manager = SessionManager()

    manager.handle(SessionCommand.START_SESSION)
    manager.handle(SessionCommand.COUNTDOWN_FINISHED)
    manager.handle(SessionCommand.ALL_PHOTOS_CAPTURED)
    manager.handle(SessionCommand.PROCESSING_FINISHED)

    assert manager.state == FotoboxState.PREVIEW


def test_print_flow() -> None:
    manager = SessionManager()

    manager.handle(SessionCommand.START_SESSION)
    manager.handle(SessionCommand.COUNTDOWN_FINISHED)
    manager.handle(SessionCommand.ALL_PHOTOS_CAPTURED)
    manager.handle(SessionCommand.PROCESSING_FINISHED)
    manager.handle(SessionCommand.PRINT)
    manager.handle(SessionCommand.PRINT_FINISHED)

    assert manager.state == FotoboxState.START


def test_restart() -> None:
    manager = SessionManager()

    manager.handle(SessionCommand.START_SESSION)
    manager.handle(SessionCommand.RESTART)

    assert manager.state == FotoboxState.START


def test_invalid_transition() -> None:
    manager = SessionManager()

    with pytest.raises(InvalidTransitionError):
        manager.handle(SessionCommand.PRINT)
