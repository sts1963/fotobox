from enum import Enum


class FotoboxState(str, Enum):
    """States of the photobooth session."""

    START = "start"
    COUNTDOWN = "countdown"
    CAPTURING = "capturing"
    PROCESSING = "processing"
    PREVIEW = "preview"
    PRINTING = "printing"
    ERROR = "error"


class SessionCommand(str, Enum):
    """Commands accepted by the session manager."""

    START_SESSION = "start_session"
    COUNTDOWN_FINISHED = "countdown_finished"
    ALL_PHOTOS_CAPTURED = "all_photos_captured"
    PROCESSING_FINISHED = "processing_finished"
    PRINT = "print"
    PRINT_FINISHED = "print_finished"
    RESTART = "restart"
    ERROR = "error"
