"""Transport capability contracts and safe device discovery."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import Context
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hano.adapters import (
    Adapters,
    mobile_catalog,
    mobile_payload,
    mobile_tag,
    resolve_endpoint,
    validate_endpoint,
)
from custom_components.hano.errors import HanoError
from custom_components.hano.models import default_config, normalize_request


def request(**extra):
    return normalize_request({"message": "Example", **extra})


@pytest.mark.parametrize(
    "priority,level",
    [
        ("quiet", "passive"),
        ("normal", "active"),
        ("important", "time-sensitive"),
        ("critical", "critical"),
    ],
)
def test_ios_priorities(priority, level):
    data = mobile_payload(request(priority=priority), "tag", {}, "ios")["data"]
    assert data["push"]["interruption-level"] == level
    assert ("sound" in data["push"]) is (priority == "critical")


@pytest.mark.parametrize("priority", ["normal", "important", "critical"])
def test_ios_custom_sound_payload(priority):
    sound = "hano_alarm_25s.wav"
    data = mobile_payload(
        request(priority=priority, ios_sound=sound), "tag", {}, "ios"
    )["data"]
    assert data == {
        "tag": "tag",
        "push": {
            "interruption-level": {
                "normal": "active",
                "important": "time-sensitive",
                "critical": "critical",
            }[priority],
            "sound": {"name": sound, "critical": 1, "volume": 1.0}
            if priority == "critical"
            else sound,
        },
    }


@pytest.mark.parametrize("priority", ["quiet", "normal", "important", "critical"])
@pytest.mark.parametrize("legacy", [False, True])
def test_ios_empty_or_missing_sound_preserves_existing_payload(priority, legacy):
    payload = request(priority=priority)
    if legacy:
        payload.pop("ios_sound")
    push = mobile_payload(payload, "tag", {}, "ios")["data"]["push"]
    if priority == "critical":
        assert push["sound"] == {"name": "default", "critical": 1, "volume": 1.0}
    else:
        assert "sound" not in push


@pytest.mark.parametrize("tag", ["x" * 65, "é" * 33, "hano_entry_" + "a" * 80])
def test_ios_tag_meets_apns_byte_limit_and_preserves_cycle_identity(tag):
    value = mobile_payload(request(), tag, {}, "ios")["data"]["tag"]
    assert len(value.encode("utf-8")) <= 64
    assert (
        value
        == mobile_payload(request(message="Updated"), tag, {}, "ios")["data"]["tag"]
    )
    assert value != mobile_tag(tag + "new-cycle", "ios")
    assert mobile_tag(tag, "android") == tag


@pytest.mark.parametrize("tag", ["short", "x" * 64, "é" * 32])
def test_valid_ios_tags_keep_their_existing_identity(tag):
    assert mobile_tag(tag, "ios") == tag


def test_android_critical_and_button_tokens():
    data = mobile_payload(
        request(
            priority="critical",
            buttons=[
                {"id": "done", "label": "Done", "resolve": True},
                {"id": "open", "label": "Open", "uri": "/lovelace"},
            ],
        ),
        "tag",
        {"done": "opaque"},
        "android",
    )["data"]
    assert data["ttl"] == 0 and data["priority"] == "high"
    assert data["channel"] == "alarm_stream" and data["confirmation"]
    assert data["actions"] == [
        {"action": "opaque", "title": "Done"},
        {"action": "URI", "title": "Open", "uri": "/lovelace"},
    ]


@pytest.mark.parametrize(
    "options",
    [
        {"image_url": "/local/picture.jpg"},
        {"priority": "critical"},
        {"buttons": [{"id": "x", "label": "X"}]},
        {"resolve_on_clear": True},
        {"ios_sound": "hano_alarm_25s.wav"},
    ],
)
async def test_generic_adapter_rejects_unsupported_options(hass, options):
    hass.states.async_set("notify.example", "unknown")
    with pytest.raises(HanoError) as error:
        validate_endpoint(
            hass, {"type": "notify", "target": "notify.example"}, request(**options)
        )
    assert error.value.code == "unsupported_options"


async def test_generic_title_is_feature_checked_and_clear_is_unsupported(hass):
    hass.states.async_set("notify.example", "unknown", {"supported_features": 0})
    endpoint = {"type": "notify", "target": "notify.example"}
    with pytest.raises(HanoError):
        validate_endpoint(hass, endpoint, request(title="Title"))
    assert await Adapters(hass).clear(endpoint, "tag", Context()) is False


@pytest.mark.parametrize(
    "platform,options",
    [
        ("ios", {"timeout": 20}),
        ("ios", {"icon": "mdi:bell"}),
        (
            "android",
            {"camera_entity_id": "camera.entry", "image_url": "/local/image.jpg"},
        ),
        ("generic", {}),
        ("android", {"ios_sound": "hano_alarm_25s.wav"}),
    ],
)
async def test_mobile_platform_limitations_fail_preflight(hass, platform, options):
    with pytest.raises(HanoError):
        validate_endpoint(
            hass,
            {"type": "mobile", "platform": platform, "device_id": "one"},
            request(**options),
        )


async def test_registered_mobile_catalog_and_notify_entity_upgrade(hass):
    entry = MockConfigEntry(
        domain="mobile_app",
        title="Example Phone",
        data={
            "device_name": "Example Phone",
            "device_id": "raw-id",
            "manufacturer": "Apple",
            "user_id": "user-id",
            "secret": "must-never-escape",
        },
    )
    entry.add_to_hass(hass)
    hass.services.async_register("notify", "mobile_app_example_phone", AsyncMock())
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("mobile_app", "raw-id")}
    )
    entity = er.async_get(hass).async_get_or_create(
        "notify", "mobile_app", "unique", config_entry=entry, device_id=device.id
    )
    rows = mobile_catalog(hass)
    assert len(rows) == 1 and "secret" not in str(rows)
    endpoint = resolve_endpoint(hass, {"type": "notify", "target": entity.entity_id})
    assert endpoint["platform"] == "ios" and endpoint["device_id"] == device.id
    with pytest.raises(HanoError, match="mismatch"):
        resolve_endpoint(
            hass,
            {
                "type": "mobile",
                "target": "notify.mobile_app_example_phone",
                "device_id": "wrong",
            },
        )


@pytest.mark.parametrize("has_own_device", [False, True])
async def test_mobile_catalog_scopes_shared_identifiers_to_registration(
    hass, has_own_device
):
    foreign_entry = MockConfigEntry(domain="mobile_app", title="Other Phone", data={})
    foreign_entry.add_to_hass(hass)
    registry = dr.async_get(hass)
    identifiers = {("mobile_app", "shared-id")}
    foreign_device = registry.async_get_or_create(
        config_entry_id=foreign_entry.entry_id, identifiers=identifiers
    )
    entry = MockConfigEntry(
        domain="mobile_app",
        title="Expected Phone",
        data={
            "device_name": "Expected Phone",
            "device_id": "shared-id",
            "manufacturer": "Apple",
        },
    )
    entry.add_to_hass(hass)
    hass.services.async_register("notify", "mobile_app_expected_phone", AsyncMock())
    own_device = (
        registry.async_get_or_create(
            config_entry_id=entry.entry_id, identifiers=identifiers
        )
        if has_own_device
        else None
    )

    rows = mobile_catalog(hass)

    if own_device is None:
        assert rows == []
    else:
        assert len(rows) == 1
        assert rows[0]["entry_id"] == entry.entry_id
        assert rows[0]["device_id"] == own_device.id
        assert rows[0]["device_id"] != foreign_device.id
        assert rows[0]["service"] == "notify.mobile_app_expected_phone"


@pytest.mark.parametrize("platform", ["ios", "android"])
async def test_camera_and_icon_are_adapted_to_mobile_platform(hass, platform):
    value = request(
        title="Entry", camera_entity_id="camera.entry", icon="mdi:door", color="#00AA88"
    )
    validate_endpoint(hass, {"type": "mobile", "platform": platform}, value)
    data = mobile_payload(value, "tag", {}, platform)["data"]
    assert data["notification_icon"] == "mdi:door" and data["color"] == "#00AA88"
    if platform == "ios":
        assert data["entity_id"] == "camera.entry"
    else:
        assert data["image"] == "/api/camera_proxy/camera.entry"


async def test_voice_without_volume_calls_tts_for_one_player(hass):
    calls = []

    async def capture(call):
        calls.append(dict(call.data))

    hass.services.async_register("tts", "speak", capture)
    hass.states.async_set("media_player.kitchen", "idle")
    await Adapters(hass).speak(
        "media_player.kitchen",
        request(tts_entity_id="tts.demo", voice_message="Spoken", tts_language="fr"),
        default_config(),
        Context(),
    )
    assert calls == [
        {
            "entity_id": "tts.demo",
            "media_player_entity_id": "media_player.kitchen",
            "message": "Spoken",
            "language": "fr",
        }
    ]


async def test_volume_requires_explicit_native_adapter_verification(hass):
    hass.states.async_set("tts.demo", "ready")
    hass.states.async_set("media_player.kitchen", "idle")
    hass.services.async_register("tts", "speak", AsyncMock())
    config = default_config() | {"tts_entity_id": "tts.demo"}
    with pytest.raises(HanoError) as error:
        Adapters(hass).validate_voice(
            request(volume=40), config, ["media_player.kitchen"]
        )
    assert error.value.code == "unsupported_volume"


async def test_volume_uses_native_announce_without_setting_global_volume(hass):
    entry = MockConfigEntry(domain="sonos", data={})
    entry.add_to_hass(hass)
    player = (
        er.async_get(hass)
        .async_get_or_create("media_player", "sonos", "speaker", config_entry=entry)
        .entity_id
    )
    hass.states.async_set(player, "playing")
    hass.states.async_set("tts.demo", "ready")
    hass.services.async_register("tts", "speak", AsyncMock())
    calls = []

    async def capture(call):
        calls.append((call.service, dict(call.data)))

    hass.services.async_register("media_player", "play_media", capture)
    config = default_config() | {
        "tts_entity_id": "tts.demo",
        "native_volume_entity_ids": [player],
    }
    # Only the optional imported TTS module is mocked; HA service dispatch is real.
    import sys
    from types import SimpleNamespace

    with patch.dict(
        sys.modules,
        {
            "homeassistant.components.tts": SimpleNamespace(
                generate_media_source_id=lambda *_args, **_kwargs: (
                    "media-source://tts/test"
                )
            )
        },
    ):
        await Adapters(hass).speak(player, request(volume=40), config, Context())
    assert calls == [
        (
            "play_media",
            {
                "entity_id": player,
                "media_content_id": "media-source://tts/test",
                "media_content_type": "music",
                "announce": True,
                "extra": {"volume": 40},
            },
        )
    ]
