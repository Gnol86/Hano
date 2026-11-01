"""Dashboard export uses durable cycles and exposes only display content."""

import asyncio
import json
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.components.recorder.db_schema import StateAttributes
from homeassistant.const import EVENT_STATE_CHANGED, STATE_UNAVAILABLE
from homeassistant.core import Event
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.hano import async_unload_entry
from custom_components.hano.errors import HanoError

ENTITY_ID = "sensor.hano_active_notifications"


def notification(**overrides):
    return {
        "notification_id": "laundry",
        "title": "Laundry",
        "message": "Ready",
        "channels": ["persistent"],
        **overrides,
    }


async def enable(manager, enabled=True):
    await manager.save(
        manager.config | {"active_notifications_sensor_enabled": enabled},
        manager.revision,
    )


@pytest.fixture
async def sensor_manager(hano_entry):
    manager = hano_entry.runtime_data
    await enable(manager)
    return manager


async def test_default_disabled_then_empty_enabled_sensor(hass, hano_entry):
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes["notifications"] == []
    await enable(hano_entry.runtime_data)
    state = hass.states.get(ENTITY_ID)
    assert state.state == "0"
    assert state.attributes["notifications"] == []
    assert "state_class" not in state.attributes
    assert "unit_of_measurement" not in state.attributes


async def test_enable_includes_existing_active_cycles_newest_first(hass, hano_entry):
    manager = hano_entry.runtime_data
    with patch(
        "custom_components.hano.manager.now", return_value="2026-11-01T10:00:00+00:00"
    ):
        await manager.send(notification())
    await manager.send(notification(notification_id="closed"))
    await manager.resolve("closed")
    with patch(
        "custom_components.hano.manager.now", return_value="2026-11-01T11:00:00+00:00"
    ):
        await manager.send(notification(notification_id="newest"))
    assert hass.states.get(ENTITY_ID).attributes["notifications"] == []
    await enable(manager)
    state = hass.states.get(ENTITY_ID)
    assert state.state == "2"
    assert [n["notification_id"] for n in state.attributes["notifications"]] == [
        "newest",
        "laundry",
    ]


async def test_updates_publish_content_at_unchanged_count(hass, sensor_manager):
    manager = sensor_manager
    first = await manager.send(notification())
    before = hass.states.get(ENTITY_ID)
    await manager.send(notification(message="Still ready", priority="important"))
    after = hass.states.get(ENTITY_ID)
    assert before.state == after.state == "1"
    assert before.attributes["notifications"][0]["message"] == "Ready"
    item = after.attributes["notifications"][0]
    assert item["message"] == "Still ready"
    assert item["priority"] == "important"
    assert item["cycle_id"] == first["cycle_id"]
    assert after is not before
    manager.notify()
    assert hass.states.get(ENTITY_ID) is after


async def test_counts_one_cycle_for_multiple_destinations_including_pending(
    hass, sensor_manager
):
    manager = sensor_manager

    async def send(_call):
        pass

    for name in ("alice", "bob"):
        hass.services.async_register("notify", f"mobile_app_{name}", send)
        hass.states.async_set(f"person.{name}", "not_home")
    await manager.save(
        manager.config
        | {
            "persons": [
                {
                    "person_id": f"person.{name}",
                    "devices": [
                        {
                            "type": "mobile",
                            "target": f"notify.mobile_app_{name}",
                            "platform": "android",
                            "device_id": name,
                        }
                    ],
                }
                for name in ("alice", "bob")
            ]
        },
        manager.revision,
    )
    result = await manager.send(
        notification(
            channels=["mobile"],
            recipient_mode="present",
            delivery="when_available",
        )
    )
    assert [d["status"] for d in result["deliveries"]] == ["pending", "pending"]
    assert hass.states.get(ENTITY_ID).state == "1"
    hass.states.async_set("person.alice", "home")
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == "1"
    assert len(hass.states.get(ENTITY_ID).attributes["notifications"]) == 1


async def test_resolution_expiration_replacement_and_purge(hass, sensor_manager):
    manager = sensor_manager
    first = await manager.send(notification())
    second = await manager.send(notification(cycle_mode="new"))
    state = hass.states.get(ENTITY_ID)
    assert state.state == "1"
    assert state.attributes["notifications"][0]["cycle_id"] == second["cycle_id"]
    assert second["cycle_id"] != first["cycle_id"]
    await manager.send(notification(notification_id="expiring", expires_in=10))
    with patch(
        "custom_components.hano.manager.dt_util.utcnow",
        return_value=dt_util.utcnow() + timedelta(seconds=20),
    ):
        await manager._expire_and_purge()
    assert manager.notifications["expiring"]["status"] == "expired"
    assert hass.states.get(ENTITY_ID).state == "1"
    await manager.purge_history()
    assert hass.states.get(ENTITY_ID).state == "1"
    await manager.resolve("laundry")
    state = hass.states.get(ENTITY_ID)
    assert state.state == "0"
    assert state.attributes["notifications"] == []


async def test_disable_clears_content_without_resolving_and_reenable_restores(
    hass, sensor_manager
):
    manager = sensor_manager
    await manager.send(notification())
    before = deepcopy(manager.notifications)
    await enable(manager, False)
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
    assert hass.states.get(ENTITY_ID).attributes["notifications"] == []
    assert manager.notifications == before
    await manager.send(notification(message="Changed while disabled"))
    assert hass.states.get(ENTITY_ID).attributes["notifications"] == []
    await enable(manager)
    assert hass.states.get(ENTITY_ID).state == "1"
    assert (
        hass.states.get(ENTITY_ID).attributes["notifications"][0]["message"]
        == "Changed while disabled"
    )


@pytest.mark.parametrize(
    "operation", ["send", "update", "resolve", "disable", "enable"]
)
async def test_failed_persistence_does_not_publish_even_during_write(
    hass, sensor_manager, operation
):
    manager = sensor_manager
    await manager.send(notification())
    if operation == "enable":
        await enable(manager, False)
    before = hass.states.get(ENTITY_ID)

    async def fail_save(_data):
        # The manager has already mutated its in-memory record at this point.
        assert hass.states.get(ENTITY_ID) is before
        raise HanoError("storage_error", "disk full")

    with patch.object(manager._store, "async_save", side_effect=fail_save):
        with pytest.raises(HanoError, match="disk full"):
            if operation == "resolve":
                await manager.resolve("laundry")
            elif operation == "disable":
                await enable(manager, False)
            elif operation == "enable":
                await enable(manager)
            else:
                await manager.send(
                    notification(
                        notification_id="other" if operation == "send" else "laundry",
                        message="Must not be published",
                    )
                )
    assert hass.states.get(ENTITY_ID) is before


async def test_initial_subscription_waits_for_durable_state(hass, sensor_manager):
    manager = sensor_manager
    await manager.send(notification())
    writing, release = asyncio.Event(), asyncio.Event()
    snapshots = []

    async def fail_save(_data):
        writing.set()
        await release.wait()
        raise HanoError("storage_error", "disk full")

    with patch.object(manager._store, "async_save", side_effect=fail_save):
        sending = hass.async_create_task(
            manager.send(notification(message="Uncommitted"))
        )
        await writing.wait()
        subscribing = hass.async_create_task(manager.async_subscribe(snapshots.append))
        try:
            await asyncio.sleep(0)
            assert not snapshots
            assert not subscribing.done()
        finally:
            release.set()
            with pytest.raises(HanoError, match="disk full"):
                await sending
            unsubscribe = await subscribing
            unsubscribe()
    assert snapshots[0]["notifications"][0]["message"] == "Ready"


async def test_allow_list_and_actual_recorder_attribute_serialization(
    hass, sensor_manager
):
    manager = sensor_manager

    async def send(_call):
        pass

    hass.services.async_register("notify", "mobile_app_alice", send)
    hass.states.async_set("person.alice", "home")
    await manager.save(
        manager.config
        | {
            "persons": [
                {
                    "person_id": "person.alice",
                    "devices": [
                        {
                            "type": "mobile",
                            "target": "notify.mobile_app_alice",
                            "platform": "android",
                            "device_id": "alice",
                        }
                    ],
                }
            ]
        },
        manager.revision,
    )
    result = await manager.send(
        notification(
            channels=["mobile", "persistent"],
            person_entity_ids=["person.alice"],
            icon="mdi:washing-machine",
            color="#123456",
            image_url="https://example.com/laundry.jpg",
            click_url="/lovelace/laundry",
            buttons=[{"id": "done", "label": "Done", "resolve": True}],
        )
    )
    state = hass.states.get(ENTITY_ID)
    item = state.attributes["notifications"][0]
    assert item == {
        "notification_id": "laundry",
        "cycle_id": result["cycle_id"],
        "title": "Laundry",
        "message": "Ready",
        "priority": "normal",
        "created_at": result["created_at"],
        "updated_at": result["updated_at"],
        "expires_at": None,
        "icon": "mdi:washing-machine",
        "color": "#123456",
        "image_url": "https://example.com/laundry.jpg",
        "click_url": "/lovelace/laundry",
    }
    serialized = StateAttributes.shared_attrs_bytes_from_event(
        Event(EVENT_STATE_CHANGED, {"new_state": state}),
        None,
    )
    assert "notifications" not in json.loads(serialized)
    assert b"Laundry" not in serialized


async def test_reload_restores_cycles_setting_and_renamed_entity(
    hass, hano_entry, sensor_manager
):
    await sensor_manager.send(notification())
    registry = er.async_get(hass)
    original = registry.async_get(ENTITY_ID)
    renamed = "sensor.my_notifications"
    registry.async_update_entity(ENTITY_ID, new_entity_id=renamed)
    await hass.async_block_till_done()
    assert hass.states.get(renamed).state == "1"
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID) is None
    assert hass.states.get(renamed).state == "1"
    assert registry.async_get(renamed).unique_id == original.unique_id
    assert not sensor_manager._listeners
    assert len(hano_entry.runtime_data._listeners) == 1
    await enable(hano_entry.runtime_data, False)
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(renamed).state == STATE_UNAVAILABLE
    assert hass.states.get(renamed).attributes["notifications"] == []
    await enable(hano_entry.runtime_data)
    assert hass.states.get(renamed).state == "1"


async def test_old_storage_defaults_off_without_losing_active_cycles(
    hass, hano_entry, sensor_manager
):
    await sensor_manager.send(notification())
    old_data = deepcopy(sensor_manager._state())
    old_data["config"].pop("active_notifications_sensor_enabled")
    await sensor_manager._store.async_save(old_data)
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
    assert hass.states.get(ENTITY_ID).attributes["notifications"] == []
    await enable(hano_entry.runtime_data)
    assert hass.states.get(ENTITY_ID).state == "1"


async def test_platform_unload_failure_keeps_manager_running(
    hass, hano_entry, sensor_manager
):
    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=False
    ):
        assert not await async_unload_entry(hass, hano_entry)
    assert not sensor_manager._stopped
    assert sensor_manager._listeners
    assert hass.data["hano"]["manager"] is sensor_manager
