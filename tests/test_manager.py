"""End-to-end decisions and durability using real HA config-entry setup."""

from copy import deepcopy
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components import persistent_notification
from homeassistant.core import Context, CoreState, Event
from homeassistant.util import dt as dt_util

from custom_components.hano.errors import HanoError
from custom_components.hano.manager import HanoManager


@pytest.fixture
async def home(hass, hano_entry):
    calls = []

    async def record(call):
        calls.append((call.service, deepcopy(dict(call.data))))

    for name in ("alice", "bob", "shared"):
        hass.services.async_register("notify", f"mobile_app_{name}", record)
    hass.states.async_set("person.alice", "home")
    hass.states.async_set("person.bob", "home")
    hass.states.async_set("binary_sensor.bob_sleep", "on")
    manager = hano_entry.runtime_data
    await manager.save(
        {
            "persons": [
                {
                    "person_id": f"person.{name}",
                    "sleep_entity_id": "binary_sensor.bob_sleep"
                    if name == "bob"
                    else "",
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
        0,
    )
    await hass.async_block_till_done()
    return manager, calls


def laundry(**overrides):
    return {
        "notification_id": "laundry",
        "title": "Laundry",
        "message": "Ready",
        "recipient_mode": "present",
        "delivery": "when_available",
        **overrides,
    }


@pytest.mark.parametrize("resolved", [False, True])
async def test_laundry_wake_sends_only_pending_or_nothing_after_resolution(
    hass, home, resolved
):
    manager, calls = home
    result = await manager.send(laundry())
    assert [d["status"] for d in result["deliveries"]] == ["accepted", "pending"]
    assert [c[0] for c in calls] == ["mobile_app_alice"]
    if resolved:
        await manager.resolve("laundry")
    hass.states.async_set("binary_sensor.bob_sleep", "off")
    await hass.async_block_till_done()
    messages = [c[0] for c in calls if c[1]["message"] != "clear_notification"]
    assert messages == (
        ["mobile_app_alice"] if resolved else ["mobile_app_alice", "mobile_app_bob"]
    )


async def test_arrival_then_wake_does_not_resend_prior_device(hass, home):
    manager, calls = home
    hass.states.async_set("person.bob", "not_home")
    await manager.send(laundry())
    hass.states.async_set("person.bob", "home")
    await hass.async_block_till_done()
    assert len(calls) == 1
    hass.states.async_set("binary_sensor.bob_sleep", "off")
    await hass.async_block_till_done()
    assert [c[0] for c in calls] == ["mobile_app_alice", "mobile_app_bob"]


@pytest.mark.parametrize("priority", ["quiet", "normal", "important", "critical"])
async def test_priority_never_overrides_sleep_without_explicit_option(home, priority):
    manager, calls = home
    await manager.send(laundry(priority=priority))
    assert len(calls) == 1
    await manager.send(laundry(priority=priority, respect_sleep=False))
    assert calls[-1][0] == "mobile_app_bob"


async def test_update_replaces_mobile_and_waiting_content_without_new_voice(hass, home):
    manager, calls = home
    hass.states.async_set("tts.demo", "ready")
    hass.states.async_set("media_player.kitchen", "idle")
    voice = AsyncMock()
    hass.services.async_register("tts", "speak", voice)
    payload = laundry(
        channels=["mobile", "voice", "persistent"],
        tts_entity_id="tts.demo",
        media_player_entity_ids=["media_player.kitchen"],
    )
    first = await manager.send(payload)
    tag = calls[0][1]["data"]["tag"]
    second = await manager.send(payload | {"message": "Updated"})
    assert first["cycle_id"] == second["cycle_id"]
    assert calls[1][1]["data"]["tag"] == tag
    assert calls[1][1]["message"] == "Updated"
    assert voice.call_count == 1
    hass.states.async_set("binary_sensor.bob_sleep", "off")
    await hass.async_block_till_done()
    assert calls[-1][1]["message"] == "Updated"
    await manager.send(payload | {"cycle_mode": "new"})
    assert voice.call_count == 2


async def test_ios_tag_update_restore_clear_and_stale_cycle(hass, home):
    """Exercise actual adapter payloads with a persisted pre-fix-length tag."""
    manager, calls = home
    config = deepcopy(manager.config)
    config["persons"][0]["devices"][0]["platform"] = "ios"
    await manager.save(config, manager.revision)
    payload = laundry(person_entity_ids=["person.alice"], recipient_mode="selected")
    await manager.send(payload)
    old_internal_tag = manager.notifications["laundry"]["_tag"]
    tag = calls[-1][1]["data"]["tag"]
    assert len(old_internal_tag.encode()) > 64
    assert len(tag.encode()) <= 64
    await manager.stop()
    restored = HanoManager(hass, manager.entry)
    await restored.load()
    try:
        assert len(calls) == 1  # No replay on restart.
        assert restored.notifications["laundry"]["_tag"] == old_internal_tag
        await restored.send(payload | {"message": "Updated"})
        assert calls[-1][1]["data"]["tag"] == tag
        await restored.resolve("laundry")
        assert calls[-1][1] == {"message": "clear_notification", "data": {"tag": tag}}
        await restored._handle_mobile_status(
            Event(
                "mobile_app_notification_cleared", {"tag": tag, "device_id": "alice"}
            ),
            "cleared",
        )
        assert (
            restored.snapshot()["notifications"][0]["deliveries"][0]["status"]
            == "cleared"
        )
        await restored.send(payload | {"resolve_on_clear": True})
        new_tag = calls[-1][1]["data"]["tag"]
        assert new_tag != tag and len(new_tag.encode()) <= 64
        await restored._handle_mobile_status(
            Event(
                "mobile_app_notification_cleared", {"tag": tag, "device_id": "alice"}
            ),
            "cleared",
        )
        assert restored.notifications["laundry"]["status"] == "active"
        await restored._handle_mobile_status(
            Event(
                "mobile_app_notification_cleared",
                {"tag": new_tag, "device_id": "alice"},
            ),
            "cleared",
        )
        assert restored.notifications["laundry"]["status"] == "resolved"
    finally:
        await restored.stop()


async def test_storage_reload_preserves_waiting_without_resending(hass, home):
    manager, calls = home
    await manager.send(laundry())
    await manager.stop()
    restored = HanoManager(hass, manager.entry)
    await restored.load()
    assert len(calls) == 1
    assert restored.snapshot()["revision"] == 1
    hass.states.async_set("binary_sensor.bob_sleep", "off")
    await hass.async_block_till_done()
    assert [c[0] for c in calls] == ["mobile_app_alice", "mobile_app_bob"]
    await restored.stop()


@pytest.mark.parametrize("name,other", [("alice", "bob"), ("bob", "alice")])
async def test_mixed_platform_mobile_events_match_tag_and_device(home, name, other):
    manager, calls = home
    config = deepcopy(manager.config)
    config["persons"][1]["devices"][0]["platform"] = "ios"
    await manager.save(config, manager.revision)
    await manager.send(laundry(respect_sleep=False))
    tags = {service: data["data"]["tag"] for service, data in calls}
    assert tags["mobile_app_alice"] != tags["mobile_app_bob"]
    tag = tags[f"mobile_app_{name}"]
    await manager._handle_mobile_status(
        Event("mobile_app_notification_received", {"tag": tag, "device_id": other}),
        "received",
    )
    record = manager.notifications["laundry"]
    assert all(d["status"] == "accepted" for d in record["deliveries"].values())
    await manager._handle_mobile_status(
        Event("mobile_app_notification_received", {"tag": tag, "device_id": name}),
        "received",
    )
    for delivery in record["deliveries"].values():
        assert delivery["status"] == (
            "received" if delivery["person_id"] == f"person.{name}" else "accepted"
        )


async def test_removing_ha_persistent_notification_resolves_only_hano(hass, home):
    manager, calls = home
    await manager.send(laundry(channels=["mobile", "persistent"]))
    persistent_notification.async_create(hass, "Other", notification_id="unrelated")
    await hass.async_block_till_done()
    persistent_notification.async_dismiss(hass, "unrelated")
    await hass.async_block_till_done()
    assert manager.notifications["laundry"]["status"] == "active"
    persistent_notification.async_dismiss(
        hass, manager.notifications["laundry"]["_tag"]
    )
    await hass.async_block_till_done()
    assert manager.notifications["laundry"]["status"] == "resolved"
    assert calls[-1][1]["message"] == "clear_notification"


async def test_dismiss_all_and_reload_do_not_loop(hass, home):
    manager, calls = home
    await manager.send(laundry(channels=["persistent"]))
    await manager.stop()
    restored = HanoManager(hass, manager.entry)
    await restored.load()
    await hass.async_block_till_done()
    assert restored.notifications["laundry"]["status"] == "active"
    persistent_notification.async_dismiss_all(hass)
    await hass.async_block_till_done()
    assert restored.notifications["laundry"]["status"] == "resolved"
    assert (
        len(
            [
                h
                for h in restored.notifications["laundry"]["history"]
                if h["event"] == "resolved"
            ]
        )
        == 1
    )
    await restored.stop()
    assert calls == []


async def test_expiration_cancels_waiting_and_history_purge_retains_active(hass, home):
    manager, calls = home
    await manager.send(laundry(expires_in=10))
    manager.notifications["laundry"]["expires_at"] = (
        dt_util.utcnow() - timedelta(seconds=1)
    ).isoformat()
    await manager._expire_and_purge()
    assert manager.notifications["laundry"]["status"] == "expired"
    assert calls[-1][1]["message"] == "clear_notification"
    await manager.send(laundry(notification_id="ongoing"))
    result = await manager.purge_history()
    assert [r["notification_id"] for r in result["notifications"]] == ["ongoing"]


async def test_invalid_requests_cannot_send_or_replace_existing_cycle(home):
    manager, calls = home
    first = await manager.send(laundry())
    with pytest.raises(HanoError, match="Expiration"):
        await manager.send(laundry(cycle_mode="new", expires_in=1e100))
    assert manager.notifications["laundry"]["cycle_id"] == first["cycle_id"]
    assert len(calls) == 1
    with pytest.raises(HanoError, match="new cycle"):
        await manager.send(laundry(recipient_mode="all"))
    assert len(calls) == 1


async def test_preview_is_side_effect_free_and_configuration_conflicts(home):
    manager, calls = home
    result = await manager.preview(laundry())
    assert result["routing"]["persons"][1]["reason"] == "sleeping"
    assert not manager.notifications and not calls
    with pytest.raises(HanoError) as conflict:
        await manager.save(manager.config, revision=0)
    assert conflict.value.code == "conflict"


async def test_storage_failure_before_send_rolls_back_without_effect(home):
    manager, calls = home
    with patch.object(manager._store, "async_save", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            await manager.send(laundry())
    assert not manager.notifications and not calls


async def test_shutdown_rejects_sends_before_any_effect(hass, home):
    manager, calls = home
    hass.set_state(CoreState.stopping)
    try:
        with pytest.raises(HanoError) as error:
            await manager.send(laundry())
        assert error.value.code == "unavailable"
        assert not manager.notifications and not calls
    finally:
        hass.set_state(CoreState.running)


@pytest.mark.parametrize("resolve_on_clear", [False, True])
async def test_android_swipe_option_and_device_confirmation(
    hass, home, resolve_on_clear
):
    manager, calls = home
    await manager.send(laundry(resolve_on_clear=resolve_on_clear))
    record = manager.notifications["laundry"]
    await manager._handle_mobile_status(
        Event(
            "mobile_app_notification_cleared",
            {"tag": record["_tag"], "device_id": "alien"},
        ),
        "cleared",
    )
    assert next(iter(record["deliveries"].values()))["status"] == "accepted"
    await manager._handle_mobile_status(
        Event(
            "mobile_app_notification_cleared",
            {"tag": record["_tag"], "device_id": "alice"},
        ),
        "cleared",
    )
    assert record["status"] == ("resolved" if resolve_on_clear else "active")


async def test_partial_transport_failure_does_not_block_other_devices(hass, home):
    manager, calls = home

    async def fail(_call):
        raise RuntimeError("fictitious failure")

    hass.services.async_register("notify", "mobile_app_alice", fail)
    result = await manager.send(laundry(respect_sleep=False))
    assert [d["status"] for d in result["deliveries"]] == ["failed", "accepted"]
    assert len(calls) == 1


async def test_shared_destination_sent_once_when_any_owner_is_eligible(home):
    manager, calls = home
    config = deepcopy(manager.config)
    config["persons"][1]["devices"] = deepcopy(config["persons"][0]["devices"])
    await manager.save(config, 1)
    result = await manager.send(laundry())
    assert len(result["deliveries"]) == len(calls) == 1


async def test_active_update_keeps_original_mapping_after_config_edit(home):
    manager, calls = home
    await manager.send(laundry())
    config = deepcopy(manager.config)
    config["persons"][0]["devices"][0]["target"] = "notify.mobile_app_shared"
    config["persons"][0]["devices"][0]["device_id"] = "shared"
    await manager.save(config, 1)
    await manager.send(laundry(message="Updated"))
    assert calls[-1][0] == "mobile_app_alice"
    await manager.send(laundry(cycle_mode="new"))
    assert calls[-1][0] == "mobile_app_shared"


async def test_buttons_without_mobile_fail_before_persistent_side_effect(home):
    manager, calls = home
    with pytest.raises(HanoError, match="mobile channel"):
        await manager.send(
            laundry(channels=["persistent"], buttons=[{"id": "done", "label": "Done"}])
        )
    assert not manager.notifications and not calls


async def test_button_failure_keeps_notification_active_and_cleans_script(hass, home):
    manager, _ = home

    async def fail(_call):
        raise RuntimeError("fictitious failure")

    hass.services.async_register("example", "fail", fail)
    await manager.send(
        laundry(
            buttons=[
                {
                    "id": "done",
                    "label": "Done",
                    "actions": [{"action": "example.fail"}],
                    "resolve": True,
                }
            ]
        )
    )
    record = manager.notifications["laundry"]
    delivery = next(iter(record["deliveries"].values()))
    await manager._handle_button(
        Event(
            "mobile_app_notification_action",
            {"action": delivery["_tokens"]["done"], "device_id": "alice"},
            context=Context(),
        )
    )
    assert record["status"] == "active"
    assert record["_button_runs"]["done"] == "failed"
    assert not manager._scripts
