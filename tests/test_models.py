"""Inputs reject ambiguous configuration before an adapter can send anything."""

import math
from copy import deepcopy

import pytest

from custom_components.hano.errors import HanoError
from custom_components.hano.models import (
    default_config,
    normalize_config,
    normalize_request,
)


@pytest.mark.parametrize("sound", ["", "hano_alarm_25s.wav", "Bell.caf", "Bell.AIFF"])
def test_ios_sound_accepts_optional_filename(sound):
    assert (
        normalize_request({"message": "Test", "ios_sound": sound})["ios_sound"] == sound
    )
    assert normalize_request({"message": "Test"})["ios_sound"] == ""


@pytest.mark.parametrize(
    "sound",
    [
        None,
        25,
        "default",
        "alarm.mp3",
        "../alarm.wav",
        "https://host/alarm.wav",
        "folder\\alarm.caf",
        "alarm:\\sound.aiff",
        " alarm.wav",
        "alarm.wav ",
        "alarm\n.wav",
        "alarm\x00.wav",
        "alarm\x7f.wav",
    ],
)
def test_ios_sound_rejects_invalid_names(sound):
    with pytest.raises(HanoError, match="ios_sound"):
        normalize_request({"message": "Test", "ios_sound": sound})


@pytest.mark.parametrize(
    "options",
    [{"priority": "quiet"}, {"channels": ["persistent"]}, {"channels": ["voice"]}],
)
def test_ios_sound_rejects_silent_or_nonmobile_requests(options):
    with pytest.raises(HanoError, match="ios_sound"):
        normalize_request({"message": "Test", "ios_sound": "alarm.wav", **options})


def test_defaults_are_independent_and_requests_preserve_caller():
    first, second = default_config(), default_config()
    first["persons"].append({"person_id": "person.alice"})
    assert second["persons"] == []
    raw = {
        "message": "Ready",
        "person_entity_ids": ["person.alice"],
        "buttons": [{"id": "done", "label": "Done", "resolve": True}],
    }
    before = deepcopy(raw)
    normalized = normalize_request(raw)
    assert normalized["reminder_interval"] == normalized["reminder_limit"] == 0
    normalized["buttons"][0]["label"] = "Changed"
    assert raw == before
    assert normalized["respect_sleep"] is True
    assert normalized["expires_in"] == 0
    assert normalized["priority"] == "normal"
    assert normalized["notification_id"] == ""


def test_configuration_normalizes_minimal_people_and_rooms():
    raw = {
        "persons": [
            {
                "person_id": "person.alice",
                "devices": [{"type": "notify", "target": "notify.example"}],
            }
        ],
        "rooms": [{"id": "living_room"}],
        "history_days": 30.0,
    }
    before = deepcopy(raw)
    config = normalize_config(raw)
    assert config["persons"][0]["sleep_entity_id"] == ""
    assert config["persons"][0]["devices"][0]["platform"] == "generic"
    assert config["rooms"][0]["media_player_entity_ids"] == []
    assert config["history_days"] == 30
    assert isinstance(config["history_days"], int)
    config["persons"][0]["devices"].clear()
    assert raw == before


@pytest.mark.parametrize(
    "value", [None, [], "", {"proximity_entity_id": "proximity.home"}]
)
def test_configuration_rejects_nonobjects_and_unknown_fields(value):
    with pytest.raises(HanoError) as error:
        normalize_config(value)
    assert error.value.code == "invalid_config"


@pytest.mark.parametrize(
    "config",
    [
        {"persons": [{"person_id": "sensor.alice"}]},
        {"persons": [{"person_id": "person.alice", "sleep_entity_id": "sensor.sleep"}]},
        {"persons": [{"person_id": "person.alice"}, {"person_id": "person.alice"}]},
        {
            "persons": [
                {
                    "person_id": "person.alice",
                    "devices": [
                        {"type": "mobile", "target": "light.bedroom"},
                    ],
                }
            ]
        },
        {
            "persons": [
                {
                    "person_id": "person.alice",
                    "devices": [
                        {
                            "type": "mobile",
                            "target": "notify.phone",
                            "platform": "windows",
                        },
                    ],
                }
            ]
        },
        {
            "persons": [
                {
                    "person_id": "person.alice",
                    "devices": [
                        {"type": "mobile", "target": "notify.phone"},
                        {"type": "mobile", "target": "notify.phone"},
                    ],
                }
            ]
        },
        {"rooms": [{"id": "living"}, {"id": "living"}]},
        {"rooms": [{"id": "living", "media_player_entity_ids": ["light.kitchen"]}]},
        {"rooms": [{"id": "living", "presence_entity_id": "person.alice"}]},
        {"tts_entity_id": "media_player.speaker"},
        {"native_volume_entity_ids": ["tts.cloud"]},
        {"history_days": 0},
        {"history_days": 2.5},
        {"history_days": True},
        {"history_days": math.inf},
        {"history_days": 3651},
        {"history_days": 10**400},
    ],
)
def test_configuration_rejects_invalid_entities_and_numbers(config):
    with pytest.raises(HanoError) as error:
        normalize_config(config)
    assert error.value.code == "invalid_config"


def test_shared_destination_across_people_remains_representable():
    config = normalize_config(
        {
            "persons": [
                {
                    "person_id": person,
                    "devices": [{"type": "notify", "target": "notify.shared"}],
                }
                for person in ("person.alice", "person.bob")
            ]
        }
    )
    assert len(config["persons"]) == 2


@pytest.mark.parametrize(
    "update",
    [
        {"message": "   "},
        {"message": None},
        {"unexpected": True},
        {"channels": []},
        {"channels": ["email"]},
        {"channels": "mobile"},
        {"respect_sleep": "false"},
        {"resolve_on_clear": 1},
        {"expires_in": -1},
        {"expires_in": math.nan},
        {"expires_in": 10**400},
        {"timeout": math.inf},
        {"volume": 101},
        {"volume": -1},
        {"volume": True},
        {"recipient_mode": "everyone"},
        {"delivery": "later"},
        {"priority": "urgent"},
        {"cycle_mode": "replace"},
        {"voice_mode": "all"},
        {"person_entity_ids": ["device_tracker.phone"]},
        {"notify_entity_ids": ["mobile_app.phone"]},
        {"mobile_device_ids": [""]},
        {"camera_entity_id": "image.front"},
        {"image_url": "javascript:alert(1)"},
        {"click_url": "data:text/html,hello"},
        {"image_url": "file:///etc/passwd"},
        {"click_url": "https:///missing-host"},
        {"image_url": "picture.jpg"},
        {"click_url": "/dashboard\nunsafe"},
        {"buttons": [{"id": "done", "label": "Done", "resolve": "true"}]},
        {"buttons": [{"id": "bad id", "label": "Done"}]},
        {"buttons": [{"id": "done", "label": ""}]},
        {
            "buttons": [
                {"id": "done", "label": "Done", "actions": {"action": "light.turn_on"}}
            ]
        },
        {"buttons": [{"id": "done", "label": "Done", "actions": ["light.turn_on"]}]},
        {"buttons": [{"id": "done", "label": "Done", "actions": [{}]}]},
        {
            "buttons": [
                {"id": "done", "label": "Done", "actions": [{"delay": math.nan}]}
            ]
        },
        {
            "buttons": [
                {"id": "done", "label": "Done", "uri": "/lovelace", "resolve": True}
            ]
        },
        {
            "buttons": [
                {
                    "id": "done",
                    "label": "Done",
                    "uri": "/lovelace",
                    "actions": [{"delay": 1}],
                }
            ]
        },
        {"buttons": [{"id": "done", "label": "A"}, {"id": "done", "label": "B"}]},
    ],
)
def test_request_rejects_invalid_inputs(update):
    with pytest.raises(HanoError) as error:
        normalize_request({"message": "Ready", **update})
    assert error.value.code == "invalid_request"


def test_button_sequences_keep_native_action_shapes_and_templates():
    sequence = [
        {
            "choose": [
                {
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "light.kitchen",
                            "state": "on",
                        }
                    ],
                    "sequence": [
                        {
                            "action": "light.turn_off",
                            "target": {"entity_id": "light.kitchen"},
                        }
                    ],
                }
            ],
            "default": [{"delay": "{{ 2 }}"}],
        }
    ]
    request = normalize_request(
        {
            "message": "Ready",
            "buttons": [
                {"id": "act", "label": "Execute", "actions": sequence, "resolve": True},
                {"id": "open", "label": "Open app", "uri": "app://com.example"},
                {"id": "event_only", "label": "Emit an event"},
            ],
        }
    )
    assert request["buttons"][0]["actions"] == sequence
    assert request["buttons"][1]["actions"] == []
    assert request["buttons"][2]["resolve"] is False


def test_deduplication_is_stable_and_priority_does_not_override_sleep():
    request = normalize_request(
        {
            "message": "Ready",
            "priority": "critical",
            "person_entity_ids": ["person.bob", "person.alice", "person.bob"],
            "channels": ["mobile", "persistent", "mobile"],
            "mobile_device_ids": ["phone", "phone"],
            "image_url": "/api/camera_proxy/camera.front",
        }
    )
    assert request["person_entity_ids"] == ["person.bob", "person.alice"]
    assert request["channels"] == ["mobile", "persistent"]
    assert request["mobile_device_ids"] == ["phone"]
    assert request["respect_sleep"] is True
