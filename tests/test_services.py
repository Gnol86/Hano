"""Native service contracts, permissions and graphical action descriptions."""

from copy import deepcopy
from unittest.mock import AsyncMock, patch

import probatio
import pytest
from homeassistant.auth.const import GROUP_ID_ADMIN
from homeassistant.core import Context, SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.service import async_get_all_descriptions
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockUser

from custom_components.hano.errors import HanoError


async def test_services_exist_before_an_entry_is_configured(hass):
    assert await async_setup_component(hass, "hano", {})
    assert hass.services.supports_response("hano", "send") is SupportsResponse.OPTIONAL
    assert hass.services.supports_response("hano", "preview") is SupportsResponse.ONLY
    assert (
        hass.services.supports_response("hano", "resolve") is SupportsResponse.OPTIONAL
    )
    with pytest.raises(ServiceValidationError, match="Configure Hano"):
        await hass.services.async_call(
            "hano", "send", {"message": "Hello"}, blocking=True
        )


async def test_optional_responses_and_context_are_forwarded(hass, hano_entry):
    context = Context()
    expected = {"notification_id": "washing", "cycle_id": "one", "deliveries": []}
    with patch.object(
        hano_entry.runtime_data, "send", AsyncMock(return_value=expected)
    ) as send:
        response = await hass.services.async_call(
            "hano",
            "send",
            {"message": "Finished"},
            blocking=True,
            return_response=True,
            context=context,
        )
        assert response == expected
        assert send.call_args.kwargs["context"] is context
        request = send.call_args.args[0]
        assert request["respect_sleep"] is True
        assert request["channels"] == ["mobile"]
        assert (
            await hass.services.async_call(
                "hano", "send", {"message": "Finished"}, blocking=True
            )
            is None
        )


@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("return_response", [False, True])
async def test_resolve_absent_native_action(hass, hano_entry, manual, return_response):
    context = Context()
    if manual:
        group = await hass.auth.async_get_group(GROUP_ID_ADMIN)
        user = MockUser(groups=[group]).add_to_hass(hass)
        context = Context(user_id=user.id)
    manager = hano_entry.runtime_data
    before = deepcopy(manager._state())
    result = await hass.services.async_call(
        "hano",
        "resolve",
        {"notification_id": "laundry"},
        blocking=True,
        return_response=return_response,
        context=context,
    )
    assert result == (
        {
            "notification_id": "laundry",
            "cycle_id": None,
            "status": "not_found",
            "changed": False,
        }
        if return_response
        else None
    )
    assert manager._state() == before


async def test_resolve_missing_then_active_then_closed_native_action(hass, hano_entry):
    manager = hano_entry.runtime_data
    first = await manager.send(
        {"notification_id": "dryer", "message": "Ready", "channels": ["persistent"]}
    )
    results = []
    for identifier in ("washer", "dryer", "dryer"):
        results.append(
            await hass.services.async_call(
                "hano",
                "resolve",
                {"notification_id": identifier},
                blocking=True,
                return_response=True,
            )
        )
    assert results[0]["status"] == "not_found"
    assert results[1]["status"] == "resolved"
    assert results[1]["cycle_id"] == first["cycle_id"]
    assert results[2] == results[1]
    assert set(manager.notifications) == {"dryer"}


async def test_resolve_requires_loaded_integration(hass):
    assert await async_setup_component(hass, "hano", {})
    with pytest.raises(ServiceValidationError) as error:
        await hass.services.async_call(
            "hano", "resolve", {"notification_id": "absent"}, blocking=True
        )
    assert error.value.translation_placeholders["code"] == "not_loaded"


@pytest.mark.parametrize("user_kind", ["unknown", "inactive_admin"])
async def test_resolve_absent_rejects_unauthorized_users(hass, hano_entry, user_kind):
    user_id = "deleted-user"
    if user_kind == "inactive_admin":
        group = await hass.auth.async_get_group(GROUP_ID_ADMIN)
        user = MockUser(groups=[group]).add_to_hass(hass)
        user.is_active = False
        user_id = user.id
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "hano",
            "resolve",
            {"notification_id": "absent"},
            blocking=True,
            context=Context(user_id=user_id),
        )


async def test_preview_requires_response_and_never_sends(hass, hano_entry):
    with (
        patch.object(
            hano_entry.runtime_data, "preview", AsyncMock(return_value={"ok": True})
        ) as preview,
        patch.object(hano_entry.runtime_data, "send", AsyncMock()) as send,
    ):
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                "hano", "preview", {"message": "Test"}, blocking=True
            )
        result = await hass.services.async_call(
            "hano", "preview", {"message": "Test"}, blocking=True, return_response=True
        )
        assert result == {"ok": True}
        preview.assert_awaited_once()
        send.assert_not_awaited()


@pytest.mark.parametrize("action", ["send", "preview"])
async def test_native_actions_preserve_custom_ios_sound(hass, hano_entry, action):
    with patch.object(
        hano_entry.runtime_data, action, AsyncMock(return_value={})
    ) as handler:
        await hass.services.async_call(
            "hano",
            action,
            {
                "message": "Test",
                "priority": "critical",
                "ios_sound": "hano_alarm_25s.wav",
            },
            blocking=True,
            return_response=True,
        )
        assert handler.call_args.args[0]["ios_sound"] == "hano_alarm_25s.wav"


async def test_read_only_user_cannot_send_preview_or_resolve(
    hass, hano_entry, hass_read_only_user
):
    for action, payload in (
        ("send", {"message": "Test"}),
        ("preview", {"message": "Test"}),
        ("resolve", {"notification_id": "private"}),
    ):
        with pytest.raises(Unauthorized):
            await hass.services.async_call(
                "hano",
                action,
                payload,
                blocking=True,
                return_response=True,
                context=Context(user_id=hass_read_only_user.id),
            )


async def test_unknown_user_cannot_send(hass, hano_entry):
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "hano",
            "send",
            {"message": "Test"},
            blocking=True,
            context=Context(user_id="deleted-user"),
        )


async def test_validation_occurs_before_send_and_error_is_localizable(hass, hano_entry):
    with patch.object(hano_entry.runtime_data, "send", AsyncMock()) as send:
        with pytest.raises(probatio.Invalid):
            await hass.services.async_call(
                "hano",
                "send",
                {"message": "Test", "priority": "invalid"},
                blocking=True,
            )
        send.assert_not_awaited()
        send.side_effect = HanoError("unsupported_option", "Volume is unavailable")
        with pytest.raises(ServiceValidationError) as failure:
            await hass.services.async_call(
                "hano", "send", {"message": "Test"}, blocking=True
            )
        assert failure.value.translation_domain == "hano"
        assert failure.value.translation_key == "operation_failed"
        assert failure.value.translation_placeholders["code"] == "unsupported_option"


async def test_native_descriptions_expose_structured_buttons(hass, hano_entry):
    descriptions = (await async_get_all_descriptions(hass))["hano"]
    for action in ("send", "preview"):
        fields = descriptions[action]["fields"]
        assert "text" in fields["availability"]["fields"]["ios_sound"]["selector"]
        assert (
            fields["lifecycle"]["fields"]["reminder_limit"]["selector"]["number"]["max"]
            == 100
        )
        assert fields["content"]["fields"]["message"]["required"]
        button = fields["buttons"]["selector"]["object"]
        assert button["multiple"] is True
        assert button["fields"]["actions"]["selector"] == {"action": {}}
        assert button["translation_key"] == "button"
        assert fields["recipients"]["fields"]["person_entity_ids"]["selector"][
            "entity"
        ]["multiple"]
