"""Export useful health counts without messages, identifiers or locations."""

from collections import Counter

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import VERSION


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Allow-list only aggregate values; do not export request or config content."""
    manager = entry.runtime_data
    snapshot = manager.snapshot()
    notifications = snapshot["notifications"]
    return {
        "version": VERSION,
        "revision": snapshot["revision"],
        "configuration": {
            "persons": len(snapshot["config"]["persons"]),
            "rooms": len(snapshot["config"]["rooms"]),
            "history_days": snapshot["config"]["history_days"],
            "tts_configured": bool(snapshot["config"]["tts_entity_id"]),
        },
        "notification_states": dict(Counter(n["status"] for n in notifications)),
        "delivery_states": dict(
            Counter(d["status"] for n in notifications for d in n["deliveries"])
        ),
    }
