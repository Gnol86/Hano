"""Deterministic decisions without proximity entities, clocks or side effects."""

import math
from copy import deepcopy

import pytest

from custom_components.hano.models import normalize_config, normalize_request
from custom_components.hano.routing import route


def person(person_id, sleep=""):
    return {"person_id": person_id, "sleep_entity_id": sleep}


def state(value, **attributes):
    return {"state": value, "attributes": attributes}


def decide(request, persons, states, *, rooms=None, home=(0, 0)):
    return route(
        normalize_request({"message": "Ready", "recipient_mode": "all", **request}),
        normalize_config({"persons": persons, "rooms": rooms or []}),
        states,
        home,
    )


def test_present_people_wait_individually_for_arrival_and_waking():
    persons = [person("person.alice"), person("person.bob", "input_boolean.sleep")]
    states = {
        "person.alice": state("home"),
        "person.bob": state("not_home"),
        "input_boolean.sleep": state("on"),
    }
    request = {"recipient_mode": "present", "delivery": "when_available"}
    result = decide(request, persons, states)["persons"]
    assert [row["eligible"] for row in result] == [True, False]
    assert result[1]["reason"] == "not_home"
    states["person.bob"] = state("home")
    assert decide(request, persons, states)["persons"][1]["reason"] == "sleeping"
    states["input_boolean.sleep"] = state("off")
    assert all(row["eligible"] for row in decide(request, persons, states)["persons"])


@pytest.mark.parametrize("mode", ["present", "absent", "nearest"])
@pytest.mark.parametrize("value", ["unknown", "unavailable", "", None])
def test_unknown_presence_is_never_home_or_absent(mode, value):
    result = decide(
        {"recipient_mode": mode},
        [person("person.alice")],
        {"person.alice": state(value, latitude=0, longitude=0)},
    )["persons"][0]
    assert not result["eligible"]
    assert result["reason"] == "unknown_presence"


def test_absent_includes_known_named_zones_but_excludes_home():
    persons = [person("person.alice"), person("person.bob"), person("person.carol")]
    result = decide(
        {"recipient_mode": "absent"},
        persons,
        {
            "person.alice": state("home"),
            "person.bob": state("work"),
            "person.carol": state("not_home"),
        },
    )["persons"]
    assert [row["eligible"] for row in result] == [False, True, True]


@pytest.mark.parametrize("value", ["unknown", "unavailable", "", "closed", None])
def test_unknown_sleep_is_not_awake(value):
    people = [person("person.alice", "binary_sensor.sleep")]
    states = {"person.alice": state("home"), "binary_sensor.sleep": state(value)}
    result = decide({}, people, states)["persons"][0]
    assert not result["eligible"]
    assert result["reason"] == "unknown_sleep"
    assert decide({"respect_sleep": False}, people, states)["persons"][0]["eligible"]


def test_selected_and_all_do_not_require_location():
    people = [person("person.alice"), person("person.bob")]
    assert all(row["eligible"] for row in decide({}, people, {})["persons"])
    result = decide(
        {"recipient_mode": "selected", "person_entity_ids": ["person.bob"]}, people, {}
    )
    assert [row["person_id"] for row in result["persons"]] == ["person.bob"]
    assert decide({"recipient_mode": "selected"}, people, {})["persons"] == []


def test_critical_priority_does_not_ignore_sleep():
    result = decide(
        {"priority": "critical"},
        [person("person.alice", "input_boolean.sleep")],
        {
            "input_boolean.sleep": state("on"),
        },
    )["persons"][0]
    assert not result["eligible"]
    assert result["reason"] == "sleeping"


def test_nearest_uses_home_zero_and_returns_all_home_ties():
    people = [person("person.alice"), person("person.bob"), person("person.carol")]
    rows = decide(
        {"recipient_mode": "nearest"},
        people,
        {
            "person.alice": state("home"),
            "person.bob": state("home", latitude=80, longitude=140),
            "person.carol": state("not_home", latitude=0, longitude=1),
        },
    )["persons"]
    assert [row["eligible"] for row in rows] == [True, True, False]
    assert [row["distance"] for row in rows[:2]] == [0, 0]
    assert rows[2]["distance"] == pytest.approx(111_195, abs=1)
    assert rows[2]["reason"] == "not_nearest"


def test_nearest_excludes_sleepers_and_keeps_explicit_candidate_subset():
    people = [
        person("person.alice", "binary_sensor.sleep"),
        person("person.bob"),
        person("person.carol"),
    ]
    states = {
        "person.alice": state("home"),
        "binary_sensor.sleep": state("on"),
        "person.bob": state("not_home", latitude=0, longitude=1),
        "person.carol": state("not_home", latitude=0, longitude=2),
    }
    rows = decide({"recipient_mode": "nearest"}, people, states)["persons"]
    assert [row["eligible"] for row in rows] == [False, True, False]
    assert rows[0]["reason"] == "sleeping"
    rows = decide(
        {"recipient_mode": "nearest", "person_entity_ids": ["person.carol"]},
        people,
        states,
    )["persons"]
    assert len(rows) == 1
    assert rows[0]["eligible"]


def test_nearest_preserves_ties_within_one_meter_deterministically():
    people = [person("person.alice"), person("person.bob")]
    states = {
        "person.alice": state("not_home", latitude=0, longitude=1),
        "person.bob": state("not_home", latitude=0, longitude=1.000001),
    }
    rows = decide({"recipient_mode": "nearest"}, people, states)["persons"]
    assert all(row["eligible"] for row in rows)
    assert [row["person_id"] for row in rows] == ["person.alice", "person.bob"]


@pytest.mark.parametrize(
    "attributes,reason",
    [
        ({}, "missing_position"),
        ({"latitude": 0}, "missing_position"),
        ({"latitude": math.nan, "longitude": 0}, "invalid_position"),
        ({"latitude": 0, "longitude": math.inf}, "invalid_position"),
        ({"latitude": 91, "longitude": 0}, "invalid_position"),
        ({"latitude": 0, "longitude": -181}, "invalid_position"),
        ({"latitude": "0", "longitude": 0}, "invalid_position"),
        ({"latitude": True, "longitude": 0}, "invalid_position"),
        ({"latitude": 10**400, "longitude": 0}, "invalid_position"),
    ],
)
def test_nearest_never_falls_back_to_arbitrary_recipients(attributes, reason):
    result = decide(
        {"recipient_mode": "nearest"},
        [person("person.alice")],
        {
            "person.alice": state("not_home", **attributes),
        },
    )["persons"][0]
    assert not result["eligible"]
    assert result["distance"] is None
    assert result["reason"] == reason


def test_nearest_invalid_home_position_is_explicit():
    result = decide(
        {"recipient_mode": "nearest"},
        [person("person.alice")],
        {
            "person.alice": state("not_home", latitude=0, longitude=1),
        },
        home=(math.nan, 0),
    )["persons"][0]
    assert result["reason"] == "invalid_home_position"


def test_occupied_voice_requires_known_occupancy_and_awake_room():
    rooms = [
        {
            "id": "living",
            "presence_entity_id": "binary_sensor.living",
            "media_player_entity_ids": ["media_player.living"],
        },
        {
            "id": "bedroom",
            "presence_entity_id": "binary_sensor.bedroom",
            "sleep_entity_id": "binary_sensor.sleep",
            "media_player_entity_ids": ["media_player.bedroom"],
        },
        {"id": "unknown", "media_player_entity_ids": ["media_player.unknown"]},
    ]
    states = {
        "binary_sensor.living": state("on"),
        "binary_sensor.bedroom": state("on"),
        "binary_sensor.sleep": state("on"),
    }
    request = {"channels": ["voice"], "voice_mode": "occupied"}
    result = decide(request, [], states, rooms=rooms)
    assert result["media_player_entity_ids"] == ["media_player.living"]
    assert result["reasons"] == [
        {"target": "bedroom", "reason": "room_sleeping"},
        {"target": "unknown", "reason": "unknown_occupancy"},
    ]
    result = decide({**request, "respect_sleep": False}, [], states, rooms=rooms)
    assert result["media_player_entity_ids"] == [
        "media_player.living",
        "media_player.bedroom",
    ]


def test_explicit_voice_checks_sleep_but_does_not_require_occupancy():
    rooms = [
        {
            "id": "bedroom",
            "sleep_entity_id": "binary_sensor.sleep",
            "media_player_entity_ids": ["media_player.bedroom"],
        }
    ]
    request = {
        "channels": ["voice"],
        "media_player_entity_ids": ["media_player.bedroom", "media_player.kitchen"],
    }
    result = decide(request, [], {}, rooms=rooms)
    assert result["media_player_entity_ids"] == ["media_player.kitchen"]
    assert result["reasons"] == [
        {"target": "media_player.bedroom", "reason": "room_unknown_sleep"}
    ]
    result = decide(request, [], {"binary_sensor.sleep": state("off")}, rooms=rooms)
    assert result["media_player_entity_ids"] == [
        "media_player.bedroom",
        "media_player.kitchen",
    ]


def test_shared_speaker_cannot_bypass_sleep_via_another_occupied_room():
    rooms = [
        {
            "id": "awake",
            "presence_entity_id": "binary_sensor.awake",
            "media_player_entity_ids": ["media_player.shared"],
        },
        {
            "id": "asleep",
            "sleep_entity_id": "binary_sensor.sleep",
            "media_player_entity_ids": ["media_player.shared"],
        },
    ]
    result = decide(
        {"channels": ["voice"], "voice_mode": "occupied"},
        [],
        {
            "binary_sensor.awake": state("on"),
            "binary_sensor.sleep": state("on"),
        },
        rooms=rooms,
    )
    assert result["media_player_entity_ids"] == []
    assert {"target": "media_player.shared", "reason": "room_sleeping"} in result[
        "reasons"
    ]


def test_routing_has_no_input_mutations_and_does_not_invent_people_for_direct_targets():
    request = normalize_request({"message": "Ready", "mobile_device_ids": ["phone"]})
    config = normalize_config(
        {"persons": [person("person.alice", "binary_sensor.sleep")]}
    )
    states = {"binary_sensor.sleep": state("on")}
    before = deepcopy((request, config, states))
    result = route(request, config, states, (0, 0))
    assert result["persons"] == []
    assert (request, config, states) == before
