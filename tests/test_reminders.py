"""Bounded reminders with a simulated clock and isolated Companion services."""

import asyncio
from copy import deepcopy
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import Event
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.hano.errors import HanoError
from custom_components.hano.manager import HanoManager
from custom_components.hano.models import normalize_request


def request(**changes):
    return {
        "notification_id": "reminder_test",
        "message": "Please acknowledge",
        "recipient_mode": "present",
        "delivery": "when_available",
        "reminder_interval": 60,
        "reminder_limit": 2,
        "buttons": [{"id": "seen", "label": "Seen", "resolve": True}],
        **changes,
    }


@pytest.fixture
async def home(hass, hano_entry, freezer):
    calls = []

    async def record(call):
        calls.append((call.service, deepcopy(dict(call.data))))

    for name in ("alice", "bob"):
        hass.services.async_register("notify", f"mobile_app_{name}", record)
        hass.states.async_set(f"person.{name}", "home")
        hass.states.async_set(f"binary_sensor.{name}_sleep", "off")
    manager = hano_entry.runtime_data
    await manager.save(
        {
            "persons": [
                {
                    "person_id": f"person.{name}",
                    "sleep_entity_id": f"binary_sensor.{name}_sleep",
                    "devices": [
                        {
                            "type": "mobile",
                            "target": f"notify.mobile_app_{name}",
                            "platform": platform,
                            "device_id": name,
                        }
                    ],
                }
                for name, platform in (("alice", "ios"), ("bob", "android"))
            ]
        },
        0,
    )
    await hass.async_block_till_done()
    return manager, calls


async def advance(manager, freezer, seconds):
    freezer.tick(timedelta(seconds=seconds))
    await manager._maintenance(None)


def notifications(calls):
    return [call for call in calls if call[1]["message"] != "clear_notification"]


def delivery(manager, name="alice"):
    return next(
        d
        for d in manager.notifications["reminder_test"]["deliveries"].values()
        if d["target"] == f"notify.mobile_app_{name}"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"reminder_interval": 0},
        {"reminder_limit": 0},
        {"reminder_interval": 59},
        {"reminder_interval": 86401},
        {"reminder_interval": 60.5},
        {"reminder_interval": True},
        {"reminder_limit": -1},
        {"reminder_limit": 101},
        {"reminder_limit": 1.5},
        {"channels": ["persistent"]},
        {"buttons": []},
        {"buttons": [{"id": "seen", "label": "Seen", "uri": "/lovelace"}]},
        {
            "buttons": [
                {
                    "id": "seen",
                    "label": "Seen",
                    "resolve": True,
                    "actions": [{"action": "light.turn_on"}],
                }
            ]
        },
    ],
)
def test_reminders_require_bounded_options_and_explicit_acknowledgement(changes):
    with pytest.raises(HanoError):
        normalize_request(request(**changes))


async def test_preview_is_inert_and_limit_is_per_destination(hass, home, freezer):
    manager, calls = home
    before = deepcopy(manager._state())
    with patch.object(manager._store, "async_save", AsyncMock()) as save:
        preview = await manager.preview(request())
        assert preview["request"]["reminder_limit"] == 2
        save.assert_not_awaited()
    assert manager._state() == before and calls == []
    await manager.send(request())
    original_tokens = deepcopy(delivery(manager)["_tokens"])
    await advance(manager, freezer, 59)
    assert len(calls) == 2
    # Exercise the registered HA timer, not only the scheduler method.
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert len(calls) == 4
    assert delivery(manager)["_tokens"] == original_tokens
    await advance(manager, freezer, 3600)
    assert len(calls) == 6  # One attempt each, no catch-up burst.
    await advance(manager, freezer, 3600)
    assert len(calls) == 6
    for row in manager.notifications["reminder_test"]["deliveries"].values():
        assert row["reminder_count"] == 2 and row["next_reminder_at"] is None


@pytest.mark.parametrize("acknowledger", ["alice", "bob"])
async def test_one_person_acknowledges_for_everyone(home, freezer, acknowledger):
    manager, calls = home
    await manager.send(request())
    token = delivery(manager, acknowledger)["_tokens"]["seen"]
    await advance(manager, freezer, 60)
    # A button from the original notification remains valid after a reminder.
    await manager._handle_button(
        Event(
            "mobile_app_notification_action",
            {"action": token, "device_id": acknowledger},
        )
    )
    assert manager.notifications["reminder_test"]["status"] == "resolved"
    assert len(notifications(calls)) == 4
    await advance(manager, freezer, 600)
    assert len(notifications(calls)) == 4
    assert all(
        d["next_reminder_at"] is None
        for d in manager.notifications["reminder_test"]["deliveries"].values()
    )


@pytest.mark.parametrize("stop", ["manual", "expiration", "replacement"])
async def test_terminal_cycle_never_reminds_and_stale_buttons_cannot_resolve_new_cycle(
    home, freezer, stop
):
    manager, calls = home
    await manager.send(request(expires_in=60 if stop == "expiration" else 0))
    old_token = delivery(manager)["_tokens"]["seen"]
    if stop == "manual":
        await manager.resolve("reminder_test")
    elif stop == "replacement":
        await manager.send(
            request(cycle_mode="new", reminder_interval=0, reminder_limit=0)
        )
        await manager._handle_button(
            Event(
                "mobile_app_notification_action",
                {"action": old_token, "device_id": "alice"},
            )
        )
        assert manager.notifications["reminder_test"]["status"] == "active"
    await advance(manager, freezer, 60)
    count = len(notifications(calls))
    assert count == (4 if stop == "replacement" else 2)
    await advance(manager, freezer, 600)
    assert len(notifications(calls)) == count


@pytest.mark.parametrize("blocked_by", ["sleep", "absence"])
async def test_reminders_respect_sleep_and_presence_without_spending_budget(
    hass, home, freezer, blocked_by
):
    manager, calls = home
    await manager.send(request())
    entity = "binary_sensor.alice_sleep" if blocked_by == "sleep" else "person.alice"
    hass.states.async_set(entity, "on" if blocked_by == "sleep" else "not_home")
    await hass.async_block_till_done()
    await advance(manager, freezer, 60)
    assert [c[0] for c in calls] == [
        "mobile_app_alice",
        "mobile_app_bob",
        "mobile_app_bob",
    ]
    assert delivery(manager).get("reminder_count", 0) == 0
    assert delivery(manager)["status"] == "accepted"
    hass.states.async_set(entity, "off" if blocked_by == "sleep" else "home")
    await hass.async_block_till_done()
    assert len(calls) == 3  # Availability alone does not create an extra reminder.
    await advance(manager, freezer, 60)
    assert delivery(manager)["reminder_count"] == 1


async def test_pending_recipient_gets_full_interval_after_initial_send(
    hass, home, freezer
):
    manager, calls = home
    hass.states.async_set("binary_sensor.bob_sleep", "on")
    await manager.send(request())
    await advance(manager, freezer, 60)
    assert [c[0] for c in calls] == ["mobile_app_alice"] * 2
    hass.states.async_set("binary_sensor.bob_sleep", "off")
    await hass.async_block_till_done()
    assert calls[-1][0] == "mobile_app_bob"
    assert delivery(manager, "bob").get("reminder_count", 0) == 0
    await advance(manager, freezer, 59)
    assert len(calls) == 3
    await advance(manager, freezer, 1)
    assert delivery(manager, "bob")["reminder_count"] == 1


async def test_restart_waits_full_interval_preserves_budget_and_skips_missed_reminders(
    hass, home, freezer
):
    manager, calls = home
    await manager.send(request())
    await advance(manager, freezer, 60)
    await manager.stop()
    freezer.tick(timedelta(hours=2))
    restored = HanoManager(hass, manager.entry)
    await restored.load()
    try:
        assert len(calls) == 4
        await advance(restored, freezer, 59)
        assert len(calls) == 4
        await advance(restored, freezer, 1)
        assert len(calls) == 6
        assert delivery(restored)["reminder_count"] == 2
        await advance(restored, freezer, 3600)
        assert len(calls) == 6
    finally:
        await restored.stop()


async def test_update_keeps_budget_resets_interval_and_can_disable(home, freezer):
    manager, calls = home
    await manager.send(request())
    await advance(manager, freezer, 60)
    freezer.tick(timedelta(seconds=30))
    await manager.send(request(message="Updated"))
    assert delivery(manager)["reminder_count"] == 1
    await advance(manager, freezer, 30)
    assert len(calls) == 6  # Update itself is an explicit send.
    await advance(manager, freezer, 30)
    assert len(calls) == 8 and calls[-1][1]["message"] == "Updated"
    await manager.send(request(reminder_interval=0, reminder_limit=0))
    await advance(manager, freezer, 3600)
    assert len(calls) == 10
    await manager.send(request())
    await advance(manager, freezer, 3600)
    assert len(calls) == 12  # Re-enabling does not reset the exhausted budget.


async def test_explicit_limit_change_and_new_cycle_control_budget(home, freezer):
    manager, calls = home
    await manager.send(request(reminder_limit=1))
    await advance(manager, freezer, 60)
    assert delivery(manager)["reminder_count"] == 1
    await manager.send(request(reminder_limit=2))
    await advance(manager, freezer, 60)
    assert delivery(manager)["reminder_count"] == 2
    await manager.send(request(reminder_limit=1))
    assert delivery(manager)["next_reminder_at"] is None
    await manager.send(request(cycle_mode="new", reminder_limit=1))
    assert delivery(manager).get("reminder_count", 0) == 0
    await advance(manager, freezer, 60)
    assert delivery(manager)["reminder_count"] == 1


async def test_update_invalidates_old_buttons_and_reminds_dismissed_destination(
    home, freezer
):
    manager, calls = home
    await manager.send(request())
    old_token = delivery(manager, "bob")["_tokens"]["seen"]
    await manager._handle_mobile_status(
        Event(
            "mobile_app_notification_cleared",
            {"tag": calls[1][1]["data"]["tag"], "device_id": "bob"},
        ),
        "cleared",
    )
    await manager.send(request(message="Changed"))
    await manager._handle_button(
        Event(
            "mobile_app_notification_action", {"action": old_token, "device_id": "bob"}
        )
    )
    assert manager.notifications["reminder_test"]["status"] == "active"
    await advance(manager, freezer, 60)
    current_token = delivery(manager, "bob")["_tokens"]["seen"]
    assert current_token != old_token
    assert calls[-1][1]["message"] == "Changed"
    await manager._handle_button(
        Event(
            "mobile_app_notification_action",
            {"action": current_token, "device_id": "bob"},
        )
    )
    assert manager.notifications["reminder_test"]["status"] == "resolved"


async def test_technical_receipt_and_local_dismissal_are_not_acknowledgements(
    home, freezer
):
    manager, calls = home
    await manager.send(request())
    tag = calls[1][1]["data"]["tag"]
    for status in ("received", "cleared"):
        await manager._handle_mobile_status(
            Event(
                "mobile_app_notification_" + status, {"tag": tag, "device_id": "bob"}
            ),
            status,
        )
        assert manager.notifications["reminder_test"]["status"] == "active"
    await advance(manager, freezer, 60)
    assert len(calls) == 4


async def test_no_voice_or_persistent_replay(hass, home, freezer):
    manager, calls = home
    hass.states.async_set("tts.demo", "ready")
    hass.states.async_set("media_player.test", "idle")
    voice = AsyncMock()
    hass.services.async_register("tts", "speak", voice)
    with patch.object(manager._adapters, "persistent") as persistent:
        await manager.send(
            request(
                channels=["mobile", "voice", "persistent"],
                tts_entity_id="tts.demo",
                media_player_entity_ids=["media_player.test"],
            )
        )
        await advance(manager, freezer, 60)
        assert len(calls) == 4
        voice.assert_awaited_once()
        persistent.assert_called_once()


async def test_failed_reminder_is_not_retried(home, freezer):
    manager, calls = home
    await manager.send(request())
    with patch.object(
        manager._adapters, "send_mobile", AsyncMock(side_effect=TimeoutError)
    ) as send:
        await advance(manager, freezer, 60)
        assert send.await_count == 2
        await advance(manager, freezer, 600)
        assert send.await_count == 2
    assert delivery(manager)["status"] == "unknown"
    assert delivery(manager)["reminder_count"] == 1
    assert delivery(manager)["next_reminder_at"] is None


async def test_interrupted_reminder_stays_unknown_after_restart(hass, home, freezer):
    manager, calls = home
    await manager.send(request())
    row = delivery(manager)
    row.update(status="updating", reminder_count=1, next_reminder_at=None)
    await manager._store.async_save(manager._state())
    await manager.stop()
    freezer.tick(timedelta(hours=1))
    restored = HanoManager(hass, manager.entry)
    await restored.load()
    try:
        assert delivery(restored)["status"] == "unknown"
        assert delivery(restored)["reminder_count"] == 1
        await advance(restored, freezer, 60)
        assert [c[0] for c in calls] == [
            "mobile_app_alice",
            "mobile_app_bob",
            "mobile_app_bob",
        ]
    finally:
        await restored.stop()


async def test_acknowledgement_cancels_unsent_recipient(hass, home, freezer):
    manager, calls = home
    hass.states.async_set("binary_sensor.bob_sleep", "on")
    await manager.send(request())
    await manager._handle_button(
        Event(
            "mobile_app_notification_action",
            {"action": delivery(manager)["_tokens"]["seen"], "device_id": "alice"},
        )
    )
    hass.states.async_set("binary_sensor.bob_sleep", "off")
    await hass.async_block_till_done()
    await advance(manager, freezer, 600)
    assert len(notifications(calls)) == 1
    assert delivery(manager, "bob")["status"] == "cancelled"


async def test_clear_opt_in_remains_global_resolution(home, freezer):
    manager, calls = home
    await manager.send(request(resolve_on_clear=True))
    await manager._handle_mobile_status(
        Event(
            "mobile_app_notification_cleared",
            {"tag": calls[1][1]["data"]["tag"], "device_id": "bob"},
        ),
        "cleared",
    )
    assert manager.notifications["reminder_test"]["status"] == "resolved"
    await advance(manager, freezer, 600)
    assert len(notifications(calls)) == 2


async def test_storage_failure_prevents_reminder_transport(home, freezer):
    manager, calls = home
    await manager.send(request())
    with patch.object(
        manager._store,
        "async_save",
        AsyncMock(side_effect=HanoError("storage_error", "disk")),
    ):
        with pytest.raises(HanoError):
            await advance(manager, freezer, 60)
    assert len(calls) == 2
    assert delivery(manager).get("reminder_count", 0) == 0


async def test_resolution_during_reminder_stops_remaining_recipients(home, freezer):
    manager, calls = home
    await manager.send(request())
    started, release = asyncio.Event(), asyncio.Event()

    async def slow_send(*args):
        started.set()
        await release.wait()

    with patch.object(manager._adapters, "send_mobile", side_effect=slow_send) as send:
        task = asyncio.create_task(advance(manager, freezer, 60))
        await started.wait()
        resolve = asyncio.create_task(manager.resolve("reminder_test"))
        for _ in range(10):
            await asyncio.sleep(0)
            if manager.notifications["reminder_test"]["status"] == "resolved":
                break
        assert manager.notifications["reminder_test"]["status"] == "resolved"
        release.set()
        await asyncio.gather(task, resolve)
        send.assert_awaited_once()
    assert all(
        d["next_reminder_at"] is None
        for d in manager.notifications["reminder_test"]["deliveries"].values()
    )
