"""Cancellation token utilities for cooperative aborts."""
from dataclasses import dataclass


@dataclass
class CancelToken:
    """Lightweight cancellation token. Call `request()` to cancel."""
    _requested: bool = False

    def request(self) -> None:
        self._requested = True

    @property
    def requested(self) -> bool:
        return bool(self._requested)

    def clear(self) -> None:
        self._requested = False


class Cancelled(Exception):
    """Raised to indicate an operation was cancelled."""
    pass
