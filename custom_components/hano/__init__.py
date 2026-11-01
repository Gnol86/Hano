"""Hano: persistent notification orchestration for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION
from .manager import HanoManager
from .panel import async_register_panel, async_remove_panel
from .services import async_register_services
from .websocket import async_register

type HanoConfigEntry = ConfigEntry[HanoManager]

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Make actions available even before an entry has finished loading."""
    async_register_services(hass)
    async_register(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HanoConfigEntry) -> bool:
    """Load the notification engine and its administrator panel."""
    data = hass.data.setdefault(DOMAIN, {})
    manager = entry.runtime_data = HanoManager(hass, entry)
    try:
        await manager.load()
        data["manager"] = manager
        await async_register_panel(hass)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        try:
            await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        finally:
            await manager.stop()
            data.pop("manager", None)
            async_remove_panel(hass)
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HanoConfigEntry) -> bool:
    """Release listeners without deleting saved notifications."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.stop()
    hass.data[DOMAIN].pop("manager", None)
    async_remove_panel(hass)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove this installation's retained configuration and notification data."""
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()
