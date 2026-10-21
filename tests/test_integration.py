"""Real lifecycle, authenticated WebSocket, privacy and subscription coverage."""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_USER
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockUser

from custom_components.hano.diagnostics import async_get_config_entry_diagnostics
from custom_components.hano.models import default_config


async def request(client, kind, **fields):
    await client.send_json_auto_id({"type": kind, **fields})
    return await client.receive_json()


async def test_config_flow_singleton(hass):
    first = await hass.config_entries.flow.async_init(
        "hano", context={"source": SOURCE_USER}
    )
    assert first["type"] is FlowResultType.FORM
    duplicate = await hass.config_entries.flow.async_init(
        "hano", context={"source": SOURCE_USER}
    )
    assert duplicate["type"] is FlowResultType.ABORT
    result = await hass.config_entries.flow.async_configure(first["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries("hano")[0]
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.config == default_config()
    again = await hass.config_entries.flow.async_init(
        "hano", context={"source": SOURCE_USER}
    )
    assert again["type"] is FlowResultType.ABORT
    assert await hass.config_entries.async_remove(entry.entry_id)


async def test_configuration_and_service_registration_survive_reload(hass, hano_entry):
    config = deepcopy(hano_entry.runtime_data.config)
    config["history_days"] = 7
    await hano_entry.runtime_data.save(config, hano_entry.runtime_data.revision)
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    assert hano_entry.runtime_data.config == config
    assert all(
        hass.services.has_service("hano", s) for s in ("send", "preview", "resolve")
    )


async def test_admin_api_validation_and_revision_conflict(
    hass, hano_entry, hass_ws_client
):
    client = await hass_ws_client(hass)
    current = await request(client, "hano/get")
    assert current["success"]
    assert current["result"]["config"] == default_config()
    revision = current["result"]["revision"]
    valid = await request(client, "hano/validate", config=default_config())
    assert valid["success"]
    assert valid["result"]["config"] == default_config()
    invalid = await request(client, "hano/validate", config={"unexpected": True})
    assert invalid["error"]["code"] == "invalid_config"
    saved = await request(
        client, "hano/save", config=default_config(), revision=revision
    )
    assert saved["success"]
    stale = await request(
        client, "hano/save", config=default_config(), revision=revision
    )
    assert stale["error"]["code"] == "conflict"
    await client.close()


@pytest.mark.parametrize("readonly", [False, True])
async def test_all_websocket_commands_require_admin(
    hass, hano_entry, hass_ws_client, hass_read_only_access_token, readonly
):
    if readonly:
        token = hass_read_only_access_token
    else:
        group = await hass.auth.async_get_group(GROUP_ID_USER)
        user = MockUser(groups=[group]).add_to_hass(hass)
        refresh = await hass.auth.async_create_refresh_token(user, "http://hano.test")
        token = hass.auth.async_create_access_token(refresh)
    client = await hass_ws_client(hass, access_token=token)
    for kind, fields in {
        "hano/get": {},
        "hano/subscribe": {},
        "hano/save": {"config": default_config(), "revision": 0},
        "hano/validate": {"config": default_config()},
        "hano/preview": {"request": {"message": "Private"}},
        "hano/send": {"request": {"message": "Private"}},
        "hano/resolve": {"notification_id": "private"},
        "hano/purge_history": {},
    }.items():
        result = await request(client, kind, **fields)
        assert result["error"]["code"] == "unauthorized", kind
        assert "result" not in result
    await client.close()


async def test_subscription_survives_reload_and_unsubscribes(
    hass, hano_entry, hass_ws_client
):
    client = await hass_ws_client(hass)
    reply = await request(client, "hano/subscribe")
    assert reply["success"]
    initial = await client.receive_json()
    assert initial["type"] == "event"
    original_manager = hano_entry.runtime_data
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    assert hano_entry.runtime_data is not original_manager
    snapshot = hano_entry.runtime_data.snapshot()
    async_dispatcher_send(hass, "hano_snapshot", snapshot)
    await hass.async_block_till_done()
    updated = await client.receive_json()
    assert updated["type"] == "event"
    assert updated["event"]["config"] == snapshot["config"]
    await client.close()
    await hass.async_block_till_done()
    # Closed subscribers must no longer be called by future manager notifications.
    async_dispatcher_send(hass, "hano_snapshot", snapshot)
    await hass.async_block_till_done()


async def test_setup_failure_cleans_manager_and_panel(hass, hano_entry):
    original_stop = type(hano_entry.runtime_data).stop
    await hass.config_entries.async_unload(hano_entry.entry_id)
    with (
        patch("custom_components.hano.async_register_panel", side_effect=OSError),
        patch(
            "custom_components.hano.HanoManager.stop",
            autospec=True,
            side_effect=original_stop,
        ) as stop,
    ):
        assert not await hass.config_entries.async_setup(hano_entry.entry_id)
    stop.assert_awaited_once()
    assert "manager" not in hass.data["hano"]


async def test_diagnostics_do_not_export_personal_payloads(hass):
    snapshot = {
        "revision": 2,
        "config": default_config() | {"persons": [{"person_id": "person.secret"}]},
        "notifications": [
            {
                "status": "active",
                "message": "SECRET MESSAGE",
                "request": {"latitude": 50.0, "device_id": "secret-device"},
                "deliveries": [{"status": "accepted", "target": "notify.secret"}],
            }
        ],
    }
    entry = SimpleNamespace(runtime_data=SimpleNamespace(snapshot=lambda: snapshot))
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["configuration"]["persons"] == 1
    assert result["notification_states"] == {"active": 1}
    assert result["delivery_states"] == {"accepted": 1}
    serialized = json.dumps(result)
    for private in ("secret", "SECRET", "50.0", "latitude", "device_id", "message"):
        assert private not in serialized


@pytest.mark.parametrize("change", ["demote", "deactivate"])
async def test_subscription_stops_when_administrator_loses_access(
    hass, hano_entry, hass_ws_client, change
):
    group = await hass.auth.async_get_group(GROUP_ID_ADMIN)
    user = MockUser(groups=[group], is_owner=False).add_to_hass(hass)
    refresh = await hass.auth.async_create_refresh_token(user, "http://hano.test")
    client = await hass_ws_client(
        hass, access_token=hass.auth.async_create_access_token(refresh)
    )
    reply = await request(client, "hano/subscribe")
    assert reply["success"]
    assert (await client.receive_json())["type"] == "event"
    if change == "demote":
        await hass.auth.async_update_user(user, group_ids=[GROUP_ID_USER])
    else:
        # Exercise the guard before Home Assistant closes a disabled user socket.
        user.is_active = False
    async_dispatcher_send(hass, "hano_snapshot", hano_entry.runtime_data.snapshot())
    await hass.async_block_till_done()
    # No private event may be queued before the next command response.
    denied = await request(client, "hano/get")
    assert denied["type"] == "result"
    assert denied["error"]["code"] == "unauthorized"
    await client.close()
