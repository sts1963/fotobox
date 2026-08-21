from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.models.state import (
    FotoboxState,
    SessionCommand,
)


@dataclass
class Session:
    """Represents one photobooth session."""

    id: str = field(
        default_factory=lambda: str(uuid4())
    )

    state: FotoboxState = FotoboxState.START

    created_at: datetime = field(
        default_factory=datetime.now
    )

    photos: list[str] = field(
        default_factory=list
    )

    collage: str | None = None
    error: str | None = None

    countdown_remaining: int | None = None

    capture_phase: str | None = None
    preview_photo: int | None = None
    next_photo_in: int | None = None


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is requested."""


class SessionManager:
    """Central state machine for the photobooth."""

    TRANSITIONS: dict[
        FotoboxState,
        dict[
            SessionCommand,
            FotoboxState,
        ],
    ] = {
        FotoboxState.START: {
            SessionCommand.START_SESSION:
                FotoboxState.COUNTDOWN,
        },

        FotoboxState.COUNTDOWN: {
            SessionCommand.COUNTDOWN_FINISHED:
                FotoboxState.CAPTURING,
        },

        FotoboxState.CAPTURING: {
            SessionCommand.ALL_PHOTOS_CAPTURED:
                FotoboxState.PROCESSING,
        },

        FotoboxState.PROCESSING: {
            SessionCommand.PROCESSING_FINISHED:
                FotoboxState.PREVIEW,
        },

        FotoboxState.PREVIEW: {
            SessionCommand.PRINT:
                FotoboxState.PRINTING,

            SessionCommand.RESTART:
                FotoboxState.START,
        },

        FotoboxState.PRINTING: {
            SessionCommand.PRINT_FINISHED:
                FotoboxState.START,
        },
    }

    def __init__(self) -> None:
        self.session = Session()

    @property
    def state(self) -> FotoboxState:
        """Return the current state."""

        return self.session.state

    def handle(
        self,
        command: SessionCommand,
    ) -> FotoboxState:
        """Process a command and return the resulting state."""

        if command == SessionCommand.ERROR:
            self.session.state = (
                FotoboxState.ERROR
            )

            self.session.countdown_remaining = None
            self.session.capture_phase = None
            self.session.preview_photo = None
            self.session.next_photo_in = None

            return self.session.state

        # Restart is intentionally possible
        # from every state.
        if command == SessionCommand.RESTART:
            self.session = Session()

            return self.session.state

        transitions = self.TRANSITIONS.get(
            self.state,
            {},
        )

        if command not in transitions:
            raise InvalidTransitionError(
                f"Command '{command.value}' "
                f"is not valid in state "
                f"'{self.state.value}'."
            )

        self.session.state = (
            transitions[command]
        )

        if self.state != FotoboxState.COUNTDOWN:
            self.session.countdown_remaining = None

        if self.state != FotoboxState.CAPTURING:
            self.session.capture_phase = None
            self.session.preview_photo = None
            self.session.next_photo_in = None

        return self.session.state

    def set_countdown(
        self,
        remaining: int,
    ) -> None:
        """Update the current countdown value."""

        if self.state != FotoboxState.COUNTDOWN:
            raise InvalidTransitionError(
                "Countdown can only be updated "
                "in COUNTDOWN state."
            )

        self.session.countdown_remaining = (
            remaining
        )

    def set_capture_feedback(
        self,
        phase: str,
        preview_photo: int | None = None,
        next_photo_in: int | None = None,
    ) -> None:
        """Update frontend feedback during photo capture."""

        if self.state != FotoboxState.CAPTURING:
            raise InvalidTransitionError(
                "Capture feedback can only be "
                "updated while capturing."
            )

        self.session.capture_phase = phase

        self.session.preview_photo = (
            preview_photo
        )

        self.session.next_photo_in = (
            next_photo_in
        )

    def add_photo(
        self,
        filename: str,
    ) -> None:
        """Register a captured photo."""

        if self.state != FotoboxState.CAPTURING:
            raise InvalidTransitionError(
                "Photos can only be added "
                "while capturing."
            )

        self.session.photos.append(
            filename
        )

    def set_collage(
        self,
        filename: str,
    ) -> None:
        """Register the generated collage."""

        if self.state != FotoboxState.PROCESSING:
            raise InvalidTransitionError(
                "A collage can only be registered "
                "while processing."
            )

        self.session.collage = filename

    def set_error(
        self,
        message: str,
    ) -> None:
        """Put the session into the error state."""

        self.session.error = message

        self.session.countdown_remaining = None
        self.session.capture_phase = None
        self.session.preview_photo = None
        self.session.next_photo_in = None

        self.session.state = (
            FotoboxState.ERROR
        )

    def snapshot(
        self,
    ) -> dict[str, Any]:
        """Return the complete frontend-visible session state."""

        session = self.session

        return {
            "type": "state",
            "state": session.state.value,
            "session_id": session.id,
            "created_at": (
                session.created_at.isoformat()
            ),
            "countdown": (
                session.countdown_remaining
            ),
            "photos": list(
                session.photos
            ),
            "collage": session.collage,
            "error": session.error,

            "capture_phase": (
                session.capture_phase
            ),
            "preview_photo": (
                session.preview_photo
            ),
            "next_photo_in": (
                session.next_photo_in
            ),
        }
