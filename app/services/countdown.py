import asyncio
from collections.abc import Awaitable, Callable


CountdownCallback = Callable[[int], Awaitable[None]]
FinishedCallback = Callable[[], Awaitable[None]]


class CountdownService:
    """Asynchronous countdown service."""

    def __init__(
        self,
        seconds: int = 5,
        on_tick: CountdownCallback | None = None,
        on_finished: FinishedCallback | None = None,
    ) -> None:
        if seconds < 1:
            raise ValueError("Countdown duration must be at least 1 second.")

        self.seconds = seconds
        self.on_tick = on_tick
        self.on_finished = on_finished

        self._task: asyncio.Task[None] | None = None

    @property
    def running(self) -> bool:
        """Return True while the countdown is running."""

        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Start the countdown."""

        if self.running:
            raise RuntimeError("Countdown is already running.")

        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Execute the countdown."""

        for remaining in range(self.seconds, 0, -1):
            if self.on_tick is not None:
                await self.on_tick(remaining)

            await asyncio.sleep(1)

        if self.on_finished is not None:
            await self.on_finished()

    async def cancel(self) -> None:
        """Cancel a running countdown."""

        if not self.running:
            return

        self._task.cancel()

        try:
            await self._task
        except asyncio.CancelledError:
            pass

        self._task = None
