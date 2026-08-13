import asyncio

import pytest

from app.services.countdown import CountdownService


@pytest.mark.asyncio
async def test_countdown_calls_tick_callback() -> None:
    ticks: list[int] = []
    finished = False

    async def on_tick(remaining: int) -> None:
        ticks.append(remaining)

    async def on_finished() -> None:
        nonlocal finished
        finished = True

    countdown = CountdownService(
        seconds=1,
        on_tick=on_tick,
        on_finished=on_finished,
    )

    await countdown.start()

    while countdown.running:
        await asyncio.sleep(0.01)

    assert ticks == [1]
    assert finished is True


@pytest.mark.asyncio
async def test_countdown_cannot_start_twice() -> None:
    countdown = CountdownService(seconds=1)

    await countdown.start()

    with pytest.raises(RuntimeError):
        await countdown.start()

    await countdown.cancel()


@pytest.mark.asyncio
async def test_countdown_can_be_cancelled() -> None:
    countdown = CountdownService(seconds=5)

    await countdown.start()

    assert countdown.running is True

    await countdown.cancel()

    assert countdown.running is False


def test_invalid_countdown_duration() -> None:
    with pytest.raises(ValueError):
        CountdownService(seconds=0)
