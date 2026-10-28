"""Regression tests for asynchronous lifecycle boundaries and callback identity."""

import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components import persistent_notification
from homeassistant.core import Context, Event

from custom_components.hano.manager import HanoManager
from custom_components.hano.models import normalize_config


class MemoryStore:
    """Copy on persistence so tests exercise restored records, not aliases."""

    def __init__(self):
        self.data = None

    async def async_load(self):
        return deepcopy(self.data)

    async def async_save(self, data):
        self.data = deepcopy(data)


@pytest.fixture
async def lifecycle_manager(hass):
    manager = HanoManager(hass, SimpleNamespace(entry_id="lifecycle"))
    manager._store = MemoryStore()
    manager.notify = Mock()
    manager._adapters.send_mobile = AsyncMock()
    manager._adapters.clear = AsyncMock(return_value=True)
    manager._adapters.speak = AsyncMock()
    manager._adapters.validate_voice = Mock()
    manager._adapters.persistent = Mock()
    manager._adapters.dismiss_persistent = Mock()
    hass.services.async_register("notify", "mobile_app_one", Mock())
    hass.services.async_register("notify", "mobile_app_two", Mock())
    hass.states.async_set("person.alice", "home")
    hass.states.async_set("person.bob", "home")
    manager.config = normalize_config(
        {
            "persons": [
                {
                    "person_id": "person.alice",
                    "devices": [
                        {
                            "type": "mobile",
                            "target": "notify.mobile_app_one",
                            "platform": "android",
                            "device_id": "one",
                        }
                    ],
                },
                {
                    "person_id": "person.bob",
                    "devices": [
                        {
                            "type": "mobile",
                            "target": "notify.mobile_app_two",
                            "platform": "ios",
                            "device_id": "two",
                        }
                    ],
                },
            ]
        }
    )
    yield manager
    await manager.stop()


def request(**extra):
    return {
        "notification_id": "washer",
        "message": "Ready",
        "person_entity_ids": ["person.alice"],
        **extra,
    }


def action_event(token):
    return Event(
        "mobile_app_notification_action", {"action": token, "device_id": "one"}
    )


async def test_new_cycle_waits_until_old_mobile_clear_completes(lifecycle_manager):
    manager = lifecycle_manager
    first = await manager.send(request())
    entered, release = asyncio.Event(), asyncio.Event()

    async def paused_clear(*_args):
        entered.set()
        await release.wait()
        return True

    manager._adapters.clear.side_effect = paused_clear
    resolving = asyncio.create_task(manager.resolve("washer"))
    await entered.wait()
    replacement = asyncio.create_task(manager.send(request(message="Second cycle")))
    await asyncio.sleep(0)
    release.set()
    await resolving
    second = await replacement
    assert second["cycle_id"] != first["cycle_id"]
    assert second["status"] == "active"
    assert second["deliveries"][0]["status"] == "accepted"
    assert manager._adapters.send_mobile.await_count == 2
    assert manager._adapters.clear.await_count == 1


async def test_resolution_cancels_remaining_destinations_after_inflight_send(
    lifecycle_manager,
):
    manager = lifecycle_manager
    entered, release = asyncio.Event(), asyncio.Event()

    async def paused_send(*_args):
        entered.set()
        await release.wait()

    manager._adapters.send_mobile.side_effect = paused_send
    sending = asyncio.create_task(
        manager.send(request(person_entity_ids=["person.alice", "person.bob"]))
    )
    await entered.wait()
    resolving = asyncio.create_task(manager.resolve("washer"))
    await asyncio.sleep(0)
    release.set()
    await sending
    result = await resolving
    assert result["status"] == "resolved"
    assert manager._adapters.send_mobile.await_count == 1
    deliveries = {item["target"]: item for item in result["deliveries"]}
    assert deliveries["notify.mobile_app_one"]["status"] == "clear_requested"
    assert deliveries["notify.mobile_app_two"]["status"] == "cancelled"


async def test_restart_does_not_replay_voice_that_never_started(lifecycle_manager):
    manager = lifecycle_manager
    normalized, decisions, endpoints = await manager._prepare(
        request(
            channels=["mobile", "voice"],
            media_player_entity_ids=["media_player.living"],
        ),
        manager.config,
    )
    record = manager._build(normalized, decisions, endpoints, Context())
    manager.notifications["washer"] = record
    await manager._store.async_save(manager._state())
    await manager.load()
    assert manager._adapters.send_mobile.await_count == 1
    manager._adapters.speak.assert_not_awaited()
    assert (
        manager.notifications["washer"]["deliveries"]["voice:media_player.living"][
            "status"
        ]
        == "skipped"
    )


async def test_delayed_persistent_removal_cannot_resolve_new_cycle(
    lifecycle_manager, monkeypatch
):
    manager = lifecycle_manager
    first = await manager.send(request(channels=["persistent"]))
    tag = manager.notifications["washer"]["_tag"]
    queued = []
    monkeypatch.setattr(manager, "_spawn", lambda coroutine: queued.append(coroutine))
    manager._persistent_changed(persistent_notification.UpdateType.REMOVED, {tag: {}})
    second = await manager.send(request(channels=["persistent"], cycle_mode="new"))
    assert first["cycle_id"] != second["cycle_id"]
    for coroutine in queued:
        await coroutine
    assert manager.notifications["washer"]["status"] == "active"


async def test_absent_resolution_and_old_callback_cannot_close_future_cycle(
    lifecycle_manager,
):
    manager = lifecycle_manager
    first = await manager.send(
        request(buttons=[{"id": "done", "label": "Done", "resolve": True}])
    )
    delivery = next(iter(manager.notifications["washer"]["deliveries"].values()))
    token = delivery["_tokens"]["done"]
    await manager.resolve("washer")
    await manager.purge_history()
    missing = await manager.resolve("washer", expected_cycle=first["cycle_id"])
    assert missing["status"] == "not_found"

    second = await manager.send(request())
    before = deepcopy(manager._state())
    stale = await manager.resolve("washer", expected_cycle=first["cycle_id"])
    assert stale == {
        "notification_id": "washer",
        "cycle_id": first["cycle_id"],
        "status": "stale",
    }
    await manager._handle_button(action_event(token))
    assert manager._state() == before
    assert second["cycle_id"] != first["cycle_id"]
    assert manager.notifications["washer"]["status"] == "active"
    assert manager._adapters.clear.await_count == 1


async def test_resolve_waits_for_concurrent_cycle_creation(lifecycle_manager):
    manager = lifecycle_manager
    transition = manager._transition_locks.setdefault("washer", asyncio.Lock())
    async with transition:
        sending = asyncio.create_task(manager.send(request()))
        await asyncio.sleep(0)
        resolving = asyncio.create_task(manager.resolve("washer"))
        await asyncio.sleep(0)
        assert not resolving.done()
    sent, resolved = await asyncio.gather(sending, resolving)
    assert resolved["cycle_id"] == sent["cycle_id"]
    assert resolved["status"] == "resolved"
    assert manager.notifications["washer"]["status"] == "resolved"


async def test_same_cycle_update_invalidates_token_waiting_for_mutation_lock(
    lifecycle_manager,
):
    manager = lifecycle_manager
    await manager.send(
        request(buttons=[{"id": "done", "label": "Done", "resolve": True}])
    )
    record = manager.notifications["washer"]
    delivery = next(iter(record["deliveries"].values()))
    token = delivery["_tokens"]["done"]
    await manager._lock.acquire()
    callback_task = asyncio.create_task(manager._handle_button(action_event(token)))
    await asyncio.sleep(0)
    delivery["_tokens"]["done"] = "HANO_new_token"
    manager._lock.release()
    await callback_task
    assert record["_button_runs"] == {}
    assert record["status"] == "active"


async def test_duplicate_button_runs_actions_once_and_old_cycle_token_is_ignored(
    lifecycle_manager, hass
):
    manager = lifecycle_manager
    performed = []

    async def perform(_call):
        performed.append(True)

    hass.services.async_register("example", "perform", perform)
    buttons = [
        {"id": "done", "label": "Done", "actions": [{"action": "example.perform"}]}
    ]
    await manager.send(request(buttons=buttons))
    delivery = next(iter(manager.notifications["washer"]["deliveries"].values()))
    token = delivery["_tokens"]["done"]
    await asyncio.gather(
        manager._handle_button(action_event(token)),
        manager._handle_button(action_event(token)),
    )
    assert performed == [True]
    await manager.send(request(buttons=buttons, cycle_mode="new"))
    await manager._handle_button(action_event(token))
    assert performed == [True]
    assert manager.notifications["washer"]["_button_runs"] == {}


async def test_interrupted_mobile_attempt_is_not_replayed(lifecycle_manager):
    manager = lifecycle_manager
    normalized, decisions, endpoints = await manager._prepare(request(), manager.config)
    record = manager._build(normalized, decisions, endpoints, Context())
    delivery = next(iter(record["deliveries"].values()))
    delivery.update(status="sending", _attempted=True)
    manager.notifications["washer"] = record
    await manager._store.async_save(manager._state())
    await manager.load()
    manager._adapters.send_mobile.assert_not_awaited()
    restored = next(iter(manager.notifications["washer"]["deliveries"].values()))
    assert restored["status"] == "unknown"
    assert restored["reason"] == "interrupted"


async def test_receipt_during_transport_is_not_downgraded_to_accepted(
    lifecycle_manager,
):
    manager = lifecycle_manager

    async def receive_before_return(_endpoint, _request, tag, _tokens, _context):
        await manager._handle_mobile_status(
            Event("mobile_app_notification_received", {"tag": tag, "device_id": "one"}),
            "received",
        )

    manager._adapters.send_mobile.side_effect = receive_before_return
    result = await manager.send(request())
    assert result["deliveries"][0]["status"] == "received"


async def test_clear_confirmation_during_transport_is_not_downgraded(lifecycle_manager):
    manager = lifecycle_manager
    await manager.send(request())

    async def clear_before_return(_endpoint, tag, _context):
        await manager._handle_mobile_status(
            Event("mobile_app_notification_cleared", {"tag": tag, "device_id": "one"}),
            "cleared",
        )
        return True

    manager._adapters.clear.side_effect = clear_before_return
    result = await manager.resolve("washer")
    assert result["deliveries"][0]["status"] == "cleared"


async def test_late_receipt_does_not_undo_clear_confirmation(lifecycle_manager):
    manager = lifecycle_manager
    await manager.send(request())
    await manager.resolve("washer")
    tag = manager.notifications["washer"]["_tag"]
    await manager._handle_mobile_status(
        Event("mobile_app_notification_cleared", {"tag": tag, "device_id": "one"}),
        "cleared",
    )
    await manager._handle_mobile_status(
        Event("mobile_app_notification_received", {"tag": tag, "device_id": "one"}),
        "received",
    )
    assert (
        next(iter(manager.notifications["washer"]["deliveries"].values()))["status"]
        == "cleared"
    )


async def test_button_can_resolve_itself_without_cancelling_remote_clear(
    lifecycle_manager, hass
):
    manager = lifecycle_manager

    async def resolve_self(call):
        await manager.resolve("washer", context=call.context)

    hass.services.async_register("example", "resolve_self", resolve_self)
    await manager.send(
        request(
            buttons=[
                {
                    "id": "done",
                    "label": "Done",
                    "actions": [{"action": "example.resolve_self"}],
                }
            ]
        )
    )
    delivery = next(iter(manager.notifications["washer"]["deliveries"].values()))
    async with asyncio.timeout(2):
        await manager._handle_button(action_event(delivery["_tokens"]["done"]))
    assert manager.notifications["washer"]["status"] == "resolved"
    manager._adapters.clear.assert_awaited_once()


async def test_room_that_falls_asleep_during_mobile_send_gets_no_voice(
    lifecycle_manager, hass
):
    manager = lifecycle_manager
    manager.config["rooms"] = normalize_config(
        {
            "rooms": [
                {
                    "id": "bedroom",
                    "sleep_entity_id": "binary_sensor.sleep",
                    "media_player_entity_ids": ["media_player.bedroom"],
                }
            ]
        }
    )["rooms"]
    hass.states.async_set("binary_sensor.sleep", "off")

    async def fall_asleep(*_args):
        hass.states.async_set("binary_sensor.sleep", "on")

    manager._adapters.send_mobile.side_effect = fall_asleep
    result = await manager.send(
        request(
            channels=["mobile", "voice"],
            media_player_entity_ids=["media_player.bedroom"],
            delivery="when_available",
        )
    )
    manager._adapters.speak.assert_not_awaited()
    voice = next(item for item in result["deliveries"] if item["channel"] == "voice")
    assert voice["status"] == "skipped"


async def test_new_cycle_stops_actions_still_running_for_an_old_button(
    lifecycle_manager, hass
):
    manager = lifecycle_manager
    entered, release = asyncio.Event(), asyncio.Event()
    performed = []

    async def paused_action(_call):
        entered.set()
        await release.wait()
        performed.append(True)

    hass.services.async_register("example", "paused_action", paused_action)
    buttons = [
        {
            "id": "done",
            "label": "Done",
            "actions": [{"action": "example.paused_action"}],
        }
    ]
    first = await manager.send(request(buttons=buttons))
    delivery = next(iter(manager.notifications["washer"]["deliveries"].values()))
    button_task = asyncio.create_task(
        manager._handle_button(action_event(delivery["_tokens"]["done"]))
    )
    await entered.wait()
    second = await manager.send(request(buttons=buttons, cycle_mode="new"))
    release.set()
    await asyncio.gather(button_task, return_exceptions=True)
    assert first["cycle_id"] != second["cycle_id"]
    assert second["status"] == "active"
    assert performed == []


async def test_shared_user_without_device_id_does_not_confirm_two_devices(
    lifecycle_manager,
):
    manager = lifecycle_manager
    await manager.send(request(person_entity_ids=["person.alice", "person.bob"]))
    record = manager.notifications["washer"]
    for delivery in record["deliveries"].values():
        delivery["_endpoint"]["user_id"] = "shared-user"
    await manager._handle_mobile_status(
        Event(
            "mobile_app_notification_received",
            {"tag": record["_tag"]},
            context=Context(user_id="shared-user"),
        ),
        "received",
    )
    assert all(item["status"] == "accepted" for item in record["deliveries"].values())
