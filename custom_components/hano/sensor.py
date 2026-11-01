"""Optional, global dashboard view of persisted active notification cycles."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HanoConfigEntry
from .manager import HanoManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HanoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Register one stable sensor, unavailable until explicitly enabled."""
    async_add_entities([ActiveNotificationsSensor(entry.runtime_data)])


class ActiveNotificationsSensor(SensorEntity):
    """Publish only display fields, never the administrator snapshot itself."""

    _attr_has_entity_name = True
    _attr_translation_key = "active_notifications"
    _attr_should_poll = False
    _attr_suggested_display_precision = 0
    _unrecorded_attributes = frozenset({"notifications"})

    def __init__(self, manager: HanoManager) -> None:
        self._manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_active_notifications"
        self.entity_id = "sensor.hano_active_notifications"
        self._attr_available = False
        self._attr_native_value = None
        self._attr_extra_state_attributes = {"notifications": []}

    @property
    def capability_attributes(self) -> dict:
        """Keep an empty fallback visible even while HA omits state attributes.

        This capability is constant: notification content is only ever written
        to extra state attributes, never to the entity registry.
        """
        return {"notifications": []}

    async def async_added_to_hass(self) -> None:
        """Read after load and subscribe only to successfully persisted changes."""
        self.async_on_remove(await self._manager.async_subscribe(self._handle_snapshot))

    @callback
    def _handle_snapshot(self, snapshot: dict) -> None:
        if self._set_snapshot(snapshot):
            self.async_write_ha_state()

    def _set_snapshot(self, snapshot: dict) -> bool:
        enabled = snapshot["config"]["active_notifications_sensor_enabled"]
        notifications = []
        if enabled:
            for record in sorted(
                (r for r in snapshot["notifications"] if r["status"] == "active"),
                key=lambda r: (r["created_at"], r["notification_id"]),
                reverse=True,
            ):
                request = record["request"]
                notifications.append(
                    {
                        "notification_id": record["notification_id"],
                        "cycle_id": record["cycle_id"],
                        "title": record["title"],
                        "message": record["message"],
                        "priority": request["priority"],
                        "created_at": record["created_at"],
                        "updated_at": record["updated_at"],
                        "expires_at": record["expires_at"],
                        "icon": request["icon"],
                        "color": request["color"],
                        "image_url": request["image_url"],
                        "click_url": request["click_url"],
                    }
                )
        attributes = {"notifications": notifications}
        if (
            self._attr_available == enabled
            and self._attr_extra_state_attributes == attributes
        ):
            return False
        self._attr_available = enabled
        self._attr_native_value = len(notifications) if enabled else None
        self._attr_extra_state_attributes = attributes
        return True
