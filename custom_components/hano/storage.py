"""Storage that acknowledges only completed writes before transport effects."""

from collections.abc import Mapping, Sequence
from typing import Any

from homeassistant.core import CoreState
from homeassistant.helpers.storage import Store
from homeassistant.util.file import WriteError
from homeassistant.util.json import SerializationError

from .errors import HanoError


class StrictStore[T: Mapping[str, Any] | Sequence[Any]](Store[T]):
    """Keep HA's format and atomic writer, but propagate durability failures.

    The standard Store logs WriteError/SerializationError without raising them.
    Hano must fail before sending when its notification intent was not persisted.
    This narrowly scoped override converts errors before the parent's catch.
    """

    def _check_running(self) -> None:
        if self.hass.state is CoreState.stopping:
            raise HanoError(
                "storage_error", "Cannot persist notification changes during shutdown"
            )

    async def async_save(self, data: T) -> None:
        """Reject shutdown deferral rather than claim a write has completed."""
        self._check_running()
        await super().async_save(data)

    async def _async_write_data(self, data: dict) -> None:
        """Propagate errors past Store's otherwise log-only error handling."""
        self._check_running()
        try:
            await super()._async_write_data(data)
        except (WriteError, SerializationError, OSError) as error:
            raise HanoError(
                "storage_error", "Notification changes could not be persisted"
            ) from error
