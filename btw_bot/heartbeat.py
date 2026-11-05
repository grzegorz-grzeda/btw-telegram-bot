"""Ping an outside dead man's switch (such as healthchecks.io) while polling works."""

import logging
import time
import urllib.error
import urllib.request
from collections.abc import Callable

INTERVAL = 5 * 60
PING_TIMEOUT = 10

log = logging.getLogger("btw_bot")


def http_ping(url: str) -> None:
    with urllib.request.urlopen(url, timeout=PING_TIMEOUT):
        pass


class Heartbeat:
    """Call beat() after each successful poll: it pings the URL at most once per INTERVAL.

    A failing ping is logged and otherwise ignored, so monitoring can never stop the bot.
    """

    def __init__(
        self,
        url: str,
        clock: Callable[[], float] = time.monotonic,
        ping: Callable[[str], None] = http_ping,
    ):
        self._url = url
        self._clock = clock
        self._ping = ping
        self._last_ping: float | None = None

    def beat(self) -> None:
        now = self._clock()
        if self._last_ping is not None and now - self._last_ping < INTERVAL:
            return
        # Counts failed pings too, so an unreachable check slows polling at most once per interval.
        self._last_ping = now
        try:
            self._ping(self._url)
        except Exception as e:
            log.warning("Heartbeat ping failed: %s", _describe(e))


def _describe(error: Exception) -> str:
    """The error without the URL: it identifies the check, so anyone holding it can ping it."""
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}"
    if isinstance(error, urllib.error.URLError):
        return str(error.reason)
    if isinstance(error, OSError):
        return str(error)
    return f"{type(error).__name__} (check BTW_HEARTBEAT_URL)"
