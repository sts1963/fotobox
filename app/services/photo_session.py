from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path

from app.core.events import EventBus
from app.models.state import SessionCommand
from app.services.camera import CameraError, CameraService
from app.services.collage import CollageError, CollageGenerator
from app.services.countdown import CountdownService
from app.services.session_manager import (
    InvalidTransitionError,
    SessionManager,
)

from app.services.background import (
    BackgroundProcessingError,
    BackgroundProcessor,
)

from app.services.background_library import (
    BackgroundLibraryService,
)

from app.services.printing import (
    PrintError,
    PrintService,
)

logger = logging.getLogger(__name__)


class PhotoSessionBusyError(Exception):
    """Raised when a photo session is already running."""


class PhotoSessionService:
    """Orchestrate one complete photo capture sequence."""

    def __init__(
        self,
        session_manager: SessionManager,
        camera_service: CameraService,
        collage_generator: CollageGenerator,
        background_processor: BackgroundProcessor,
        background_library_service: BackgroundLibraryService,
        print_service: PrintService,
        event_bus: EventBus,
        session_root: Path = Path("data/sessions"),
        logo_path: Path = Path("assets/logo.png"),
        background_enabled: bool = False,
        background_selection_mode: str = "fixed",
        background_images: tuple[Path, ...] = (),
        countdown_seconds: int = 5,
        photo_count: int = 3,
        interval_seconds: float = 3.0,
    ) -> None:
        self.session_manager = session_manager
        self.camera_service = camera_service
        self.collage_generator = collage_generator
        self.event_bus = event_bus
        self.background_processor = background_processor
        self.background_library_service = (
            background_library_service
        )
        self.background_enabled = background_enabled
        self.background_selection_mode = (
            background_selection_mode
        )
        self.background_images = background_images
        self.session_root = session_root
        self.logo_path = logo_path

        self.countdown_seconds = countdown_seconds
        self.photo_count = photo_count
        self.interval_seconds = interval_seconds

        self._task: asyncio.Task[None] | None = None
        self._start_lock = asyncio.Lock()
        self.print_service = print_service

    @property
    def backgrounds_enabled(self) -> bool:
        """Return whether virtual backgrounds are enabled."""

        return self.background_enabled

    def set_backgrounds_enabled(
        self,
        enabled: bool,
    ) -> None:
        """Enable or disable virtual backgrounds at runtime."""

        self.background_enabled = enabled

        logger.info(
            "Virtual backgrounds %s",
            "enabled"
            if enabled
            else "disabled",
        )

    @property
    def background_selection(self) -> str:
        """Return the current background selection mode."""

        return self.background_selection_mode

    def set_background_selection_mode(
        self,
        mode: str,
    ) -> None:
        """Change the background selection mode at runtime."""

        if mode not in (
            "fixed",
            "random",
        ):
            raise ValueError(
                "Background selection mode must be "
                "'fixed' or 'random'."
            )

        self.background_selection_mode = mode

        logger.info(
            "Background selection mode changed: %s",
            mode,
        )

    @property
    def running(self) -> bool:
        """Return whether a photo sequence is currently running."""

        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Start a new photo session."""

        async with self._start_lock:
            if self.running:
                raise PhotoSessionBusyError(
                    "A photo session is already running."
                )

            if not self.camera_service.available:
                self.session_manager.set_error(
                    "Camera is not available."
                )

                logger.error(
                    "Unable to start photo session: "
                    "camera is not available"
                )

                await self._publish_state()
                return

            try:
                self.session_manager.handle(
                    SessionCommand.START_SESSION
                )

            except InvalidTransitionError as exc:
                logger.warning(
                    "Unable to start photo session: %s",
                    exc,
                )

                raise PhotoSessionBusyError(
                    "The photobooth is not ready "
                    "for a new session."
                ) from exc

            logger.info(
                "Photo session started: session_id=%s",
                self.session_manager.session.id,
            )

            await self._publish_state()

            self._task = asyncio.create_task(
                self._run(),
                name="photo-session",
            )

    async def restart(self) -> None:
        """Cancel the current sequence and reset the session."""

        task = self._task

        if task is not None and not task.done():
            logger.info(
                "Cancelling running photo session: "
                "session_id=%s",
                self.session_manager.session.id,
            )

            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

        self._task = None

        self.session_manager.handle(
            SessionCommand.RESTART
        )

        logger.info(
            "Photo session reset: new_session_id=%s",
            self.session_manager.session.id,
        )

        await self._publish_state()

    async def wait_until_idle(self) -> None:
        """Wait until the active session task has finished."""

        task = self._task

        if task is not None:
            await task

    async def _run(self) -> None:
        """Run countdown, photo sequence and collage generation."""

        countdown: CountdownService | None = None

        try:
            countdown = CountdownService(
                seconds=self.countdown_seconds,
                on_tick=self._countdown_tick,
                on_finished=self._countdown_finished,
            )

            await countdown.start()

            while countdown.running:
                await asyncio.sleep(0.05)

            await self._capture_photos()

            photo_paths = await self._prepare_photos()

            await self._create_collage(
                photo_paths
            )

        except asyncio.CancelledError:
            if countdown is not None:
                await countdown.cancel()

            logger.info(
                "Photo session cancelled: session_id=%s",
                self.session_manager.session.id,
            )

            raise

        except (
            CameraError,
            CollageError,
            BackgroundProcessingError,
            InvalidTransitionError,
        ) as exc:
            logger.error(
                "Photo session failed: "
                "session_id=%s error=%s",
                self.session_manager.session.id,
                exc,
            )

            self.session_manager.set_error(
                str(exc)
            )

            await self._publish_state()

        except Exception as exc:
            logger.exception(
                "Unexpected photo session error: "
                "session_id=%s",
                self.session_manager.session.id,
            )

            self.session_manager.set_error(
                f"Unexpected photo session error: {exc}"
            )

            await self._publish_state()

        finally:
            self._task = None

    async def _countdown_tick(
        self,
        remaining: int,
    ) -> None:
        """Update and publish one countdown step."""

        self.session_manager.set_countdown(
            remaining
        )

        await self._publish_state()

    async def _countdown_finished(self) -> None:
        """Move the session into CAPTURING."""

        self.session_manager.handle(
            SessionCommand.COUNTDOWN_FINISHED
        )

        self.session_manager.set_capture_feedback(
            phase="capturing",
        )

        logger.info(
            "Countdown finished: session_id=%s",
            self.session_manager.session.id,
        )

        await self._publish_state()

    async def _capture_photos(self) -> None:
        """Capture all configured photos."""

        session_id = (
            self.session_manager.session.id
        )

        session_directory = (
            self.session_root / session_id
        )

        session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for number in range(
            1,
            self.photo_count + 1,
        ):
            self.session_manager.set_capture_feedback(
                phase="capturing",
            )

            await self._publish_state()

            filename = (
                session_directory
                / f"photo_{number:02d}.jpg"
            )

            await asyncio.to_thread(
                self.camera_service.capture_photo,
                filename,
            )

            logger.info(
                "Photo captured: "
                "session_id=%s photo=%s path=%s",
                session_id,
                number,
                filename,
            )

            self.session_manager.add_photo(
                str(filename)
            )

            if number < self.photo_count:
                #
                # Show the captured photo for two seconds.
                #
                self.session_manager.set_capture_feedback(
                    phase="preview",
                    preview_photo=number,
                )

                await self._publish_state()

                preview_seconds = min(
                    2.0,
                    self.interval_seconds,
                )

                await asyncio.sleep(
                    preview_seconds
                )

                #
                # Use the remaining interval as a visible
                # countdown for the next photo.
                #
                remaining_seconds = max(
                    0,
                    int(
                        round(
                            self.interval_seconds
                            - preview_seconds
                        )
                    ),
                )

                for remaining in range(
                    remaining_seconds,
                    0,
                    -1,
                ):
                    self.session_manager.set_capture_feedback(
                        phase="waiting",
                        next_photo_in=remaining,
                    )

                    await self._publish_state()

                    await asyncio.sleep(1)

            else:
                await self._publish_state()

        self.session_manager.handle(
            SessionCommand.ALL_PHOTOS_CAPTURED
        )

        logger.info(
            "All photos captured: session_id=%s",
            session_id,
        )

        await self._publish_state()

    def _select_backgrounds(
        self,
        photo_count: int,
    ) -> list[Path]:
        """Return the backgrounds to use for one session."""

        if self.background_selection_mode == "fixed":
            if len(self.background_images) != photo_count:
                raise BackgroundProcessingError(
                    "Number of configured background images "
                    "does not match number of photos."
                )

            return list(
                self.background_images
            )

        if self.background_selection_mode == "random":
            filenames = (
                self.background_library_service
                .list_backgrounds()
            )

            if len(filenames) < photo_count:
                raise BackgroundProcessingError(
                    "At least three background images "
                    "are required for random selection."
                )

            selected = random.sample(
                filenames,
                k=photo_count,
            )

            return [
                (
                    self.background_library_service
                    .library_directory
                    / filename
                )
                for filename in selected
            ]

        raise BackgroundProcessingError(
            "Unknown background selection mode."
        )

    async def _prepare_photos(
        self,
    ) -> list[Path]:
        """Return original or background-processed photos."""

        session = self.session_manager.session

        original_paths = [
            Path(filename)
            for filename in session.photos
        ]

        if not self.background_enabled:
            logger.info(
                "Virtual backgrounds disabled: "
                "session_id=%s",
                session.id,
            )

            return original_paths

        background_paths = (
            self._select_backgrounds(
                len(original_paths)
            )
        )

        logger.info(
            "Applying virtual backgrounds: "
            "session_id=%s selection_mode=%s",
            session.id,
            self.background_selection_mode,
        )

        processed_paths: list[Path] = []

        session_directory = (
            self.session_root / session.id
        )

        for number, (
            photo_path,
            background_path,
        ) in enumerate(
            zip(
                original_paths,
                background_paths,
                strict=True,
            ),
            start=1,
        ):
            output_path = (
                session_directory
                / f"processed_{number:02d}.jpg"
            )

            result = await asyncio.to_thread(
                self.background_processor.replace_greenscreen,
                photo_path,
                background_path,
                output_path,
            )

            processed_paths.append(
                result
            )

            logger.info(
                "Virtual background applied: "
                "session_id=%s photo=%s background=%s",
                session.id,
                number,
                background_path,
            )

        return processed_paths

    async def _create_collage(
        self,
        photo_paths: list[Path],
    ) -> None:
        """Generate the 2x2 collage for the current session."""

        session = (
            self.session_manager.session
        )

        if len(photo_paths) != 3:
            raise CollageError(
                "Exactly three captured photos are required."
            )

        session_directory = (
            self.session_root / session.id
        )

        output_path = (
            session_directory
            / "collage.jpg"
        )

        logger.info(
            "Creating collage: "
            "session_id=%s output=%s",
            session.id,
            output_path,
        )

        result = await asyncio.to_thread(
            self.collage_generator.create_grid_2x2,
            photo_paths,
            output_path,
            self.logo_path,
        )

        self.session_manager.set_collage(
            str(result)
        )

        self.session_manager.handle(
            SessionCommand.PROCESSING_FINISHED
        )

        logger.info(
            "Collage created: "
            "session_id=%s path=%s",
            session.id,
            result,
        )

        await self._publish_state()

    async def print_collage(self) -> None:
       """Print the collage of the current session."""

       session = self.session_manager.session

       if session.collage is None:
           raise PrintError(
               "No collage is available for printing."
           )

       try:
           self.session_manager.handle(
               SessionCommand.PRINT
           )

           await self._publish_state()

           logger.info(
               "Printing collage: "
               "session_id=%s path=%s",
               session.id,
               session.collage,
           )

           job_info = await asyncio.to_thread(
               self.print_service.print_collage,
               Path(session.collage),
           )

           logger.info(
               "Collage submitted to printer: "
               "session_id=%s job=%s",
               session.id,
               job_info,
           )

           self.session_manager.handle(
               SessionCommand.PRINT_FINISHED
           )

           await self._publish_state()

       except (
           PrintError,
           InvalidTransitionError,
       ) as exc:
           logger.error(
               "Printing failed: "
               "session_id=%s error=%s",
               session.id,
               exc,
           )

           self.session_manager.set_error(
               str(exc)
           )

           await self._publish_state()
   
    async def _publish_state(self) -> None:
        """Publish the current session state."""

        await self.event_bus.publish(
            self.session_manager.snapshot()
        )
