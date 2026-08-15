from collections.abc import Awaitable, Callable
from typing import Any


EventData = dict[str, Any]
EventCallback = Callable[[EventData], Awaitable[None]]


class EventBus:
    """Distribute application events to connected clients."""

    def __init__(self) -> None:
        self._subscribers: set[EventCallback] = set()

    def subscribe(self, callback: EventCallback) -> None:
        """Register an event subscriber."""

        self._subscribers.add(callback)

    def unsubscribe(self, callback: EventCallback) -> None:
        """Remove an event subscriber."""

        self._subscribers.discard(callback)

    async def publish(self, event: EventData) -> None:
        """Publish an event to all current subscribers."""

        for callback in tuple(self._subscribers):
            try:
                await callback(event)
            except Exception:
                # A disconnected client must never interrupt
                # the photobooth workflow.
                pass

