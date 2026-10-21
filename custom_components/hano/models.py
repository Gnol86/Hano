"""Validated, JSON-compatible configuration and action inputs.

This module deliberately has no Home Assistant dependency. Validation here checks
the public shape; integration code validates action sequences and live entities.
"""

import math
import re
from copy import deepcopy
from typing import Any
from urllib.parse import urlsplit

from .errors import HanoError

_ENTITY = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z0-9_]+$")
_SLUG = re.compile(r"^[A-Za-z0-9_-]+$")
_PERSON_KEYS = {"person_id", "name", "sleep_entity_id", "devices"}
_DEVICE_KEYS = {"type", "target", "platform", "device_id"}
_ROOM_KEYS = {
    "id",
    "name",
    "presence_entity_id",
    "sleep_entity_id",
    "media_player_entity_ids",
}
_BUTTON_KEYS = {"id", "label", "uri", "actions", "resolve"}
_SENSOR_DOMAINS = {"binary_sensor", "input_boolean"}


def default_config() -> dict[str, Any]:
    """Return a fresh default configuration on each call."""
    return {
        "persons": [],
        "rooms": [],
        "tts_entity_id": "",
        "tts_language": "",
        "history_days": 30,
        "native_volume_entity_ids": [],
    }


def _fail(code: str, field: str, requirement: str) -> None:
    raise HanoError(code, f"{field}: {requirement}")


def _mapping(value: Any, allowed: set[str], code: str, field: str) -> dict:
    if not isinstance(value, dict):
        _fail(code, field, "must be an object")
    unknown = set(value) - allowed
    if unknown:
        _fail(code, field, f"unknown fields: {', '.join(sorted(map(str, unknown)))}")
    return value


def _text(value: Any, code: str, field: str, *, required: bool = False) -> str:
    if not isinstance(value, str) or (required and not value.strip()):
        _fail(code, field, "must be a nonempty string" if required else "must be text")
    return value


def _boolean(value: Any, code: str, field: str) -> bool:
    if not isinstance(value, bool):
        _fail(code, field, "must be true or false")
    return value


def _number(
    value: Any,
    code: str,
    field: str,
    *,
    minimum: float = 0,
    maximum: float | None = None,
    integer: bool = False,
) -> int | float:
    try:
        finite = isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        finite = False
    if (
        isinstance(value, bool)
        or not finite
        or value < minimum
        or (maximum is not None and value > maximum)
        or (integer and int(value) != value)
    ):
        _fail(code, field, "must be a finite number within the allowed range")
    return int(value) if integer else value


def _choice(value: Any, choices: set[str], code: str, field: str) -> str:
    if not isinstance(value, str) or value not in choices:
        _fail(code, field, f"must be one of {', '.join(sorted(choices))}")
    return value


def _entity(
    value: Any,
    domains: set[str],
    code: str,
    field: str,
    *,
    optional: bool = False,
) -> str:
    value = _text(value, code, field)
    if optional and value == "":
        return value
    if not _ENTITY.fullmatch(value) or value.partition(".")[0] not in domains:
        _fail(code, field, f"must be an entity in {', '.join(sorted(domains))}")
    return value


def _list(value: Any, code: str, field: str) -> list:
    if not isinstance(value, list):
        _fail(code, field, "must be a list")
    return value


def _entities(value: Any, domains: set[str], code: str, field: str) -> list[str]:
    return list(
        dict.fromkeys(
            _entity(item, domains, code, f"{field}[{index}]")
            for index, item in enumerate(_list(value, code, field))
        )
    )


def _url(value: Any, code: str, field: str, *, image: bool = False) -> str:
    value = _text(value, code, field)
    if not value:
        return value
    if any(ord(character) < 32 for character in value):
        _fail(code, field, "must not contain control characters")
    try:
        parsed = urlsplit(value)
    except ValueError:
        _fail(code, field, "must be a valid URL or local path")
    if parsed.scheme.lower() in {"javascript", "data", "vbscript", "file"}:
        _fail(code, field, "URL scheme is not supported")
    if image and parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        _fail(code, field, "images must use HTTP, HTTPS or a local path")
    if not parsed.scheme and not value.startswith("/"):
        _fail(code, field, "relative URLs must start with /")
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        _fail(code, field, "HTTP URLs require a host")
    return value


def _json(value: Any, code: str, field: str) -> None:
    """Reject non-persistable action payloads without interpreting HA scripts."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float) and math.isfinite(value):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json(item, code, f"{field}[{index}]")
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for key, item in value.items():
            _json(item, code, f"{field}.{key}")
        return
    _fail(code, field, "must contain only JSON-compatible values")


def normalize_config(value: Any) -> dict[str, Any]:
    """Validate and copy a complete or partially specified configuration."""
    code = "invalid_config"
    result = default_config()
    result.update(deepcopy(_mapping(value, set(result), code, "config")))
    persons = []
    seen_persons: set[str] = set()
    for index, raw in enumerate(_list(result["persons"], code, "persons")):
        field = f"persons[{index}]"
        person = {"name": "", "sleep_entity_id": "", "devices": []}
        person.update(_mapping(raw, _PERSON_KEYS, code, field))
        person_id = _entity(person.get("person_id"), {"person"}, code, field)
        if person_id in seen_persons:
            _fail(code, field, "person is configured more than once")
        seen_persons.add(person_id)
        _text(person["name"], code, f"{field}.name")
        _entity(
            person["sleep_entity_id"],
            _SENSOR_DOMAINS,
            code,
            f"{field}.sleep_entity_id",
            optional=True,
        )
        devices = []
        seen_devices: set[tuple[str, str]] = set()
        for device_index, raw_device in enumerate(
            _list(person["devices"], code, f"{field}.devices")
        ):
            device_field = f"{field}.devices[{device_index}]"
            device = {"platform": "generic", "device_id": ""}
            device.update(_mapping(raw_device, _DEVICE_KEYS, code, device_field))
            _choice(
                device.get("type"), {"mobile", "notify"}, code, f"{device_field}.type"
            )
            _entity(device.get("target"), {"notify"}, code, f"{device_field}.target")
            _choice(
                device["platform"],
                {"ios", "android", "generic"},
                code,
                f"{device_field}.platform",
            )
            _text(device["device_id"], code, f"{device_field}.device_id")
            identity = (device["type"], device["target"])
            if identity in seen_devices:
                _fail(code, device_field, "device is configured twice for this person")
            seen_devices.add(identity)
            devices.append(device)
        person["devices"] = devices
        persons.append(person)
    result["persons"] = persons

    rooms = []
    seen_rooms: set[str] = set()
    for index, raw in enumerate(_list(result["rooms"], code, "rooms")):
        field = f"rooms[{index}]"
        room = {
            "name": "",
            "presence_entity_id": "",
            "sleep_entity_id": "",
            "media_player_entity_ids": [],
        }
        room.update(_mapping(raw, _ROOM_KEYS, code, field))
        room_id = _text(room.get("id"), code, f"{field}.id", required=True)
        if not _SLUG.fullmatch(room_id):
            _fail(
                code,
                f"{field}.id",
                "must be a stable identifier using letters, digits, _ or -",
            )
        if room_id in seen_rooms:
            _fail(code, field, "room is configured more than once")
        seen_rooms.add(room_id)
        _text(room["name"], code, f"{field}.name")
        for sensor in ("presence_entity_id", "sleep_entity_id"):
            _entity(
                room[sensor], _SENSOR_DOMAINS, code, f"{field}.{sensor}", optional=True
            )
        room["media_player_entity_ids"] = _entities(
            room["media_player_entity_ids"],
            {"media_player"},
            code,
            f"{field}.media_player_entity_ids",
        )
        rooms.append(room)
    result["rooms"] = rooms
    _entity(result["tts_entity_id"], {"tts"}, code, "tts_entity_id", optional=True)
    _text(result["tts_language"], code, "tts_language")
    result["history_days"] = _number(
        result["history_days"],
        code,
        "history_days",
        minimum=1,
        maximum=3650,
        integer=True,
    )
    result["native_volume_entity_ids"] = _entities(
        result["native_volume_entity_ids"],
        {"media_player"},
        code,
        "native_volume_entity_ids",
    )
    return result


def normalize_request(value: Any) -> dict[str, Any]:
    """Validate an action, applying defaults without mutating the caller."""
    code = "invalid_request"
    result: dict[str, Any] = {
        "notification_id": "",
        "title": "",
        "message": "",
        "recipient_mode": "selected",
        "person_entity_ids": [],
        "notify_entity_ids": [],
        "mobile_device_ids": [],
        "channels": ["mobile"],
        "respect_sleep": True,
        "delivery": "immediate",
        "priority": "normal",
        "cycle_mode": "update",
        "expires_in": 0,
        "resolve_on_clear": False,
        "image_url": "",
        "click_url": "",
        "camera_entity_id": "",
        "icon": "",
        "color": "",
        "timeout": 0,
        "voice_mode": "explicit",
        "media_player_entity_ids": [],
        "tts_entity_id": "",
        "tts_language": "",
        "voice_message": "",
        "volume": None,
        "buttons": [],
    }
    result.update(deepcopy(_mapping(value, set(result), code, "request")))
    for field in (
        "notification_id",
        "title",
        "message",
        "icon",
        "color",
        "tts_language",
        "voice_message",
    ):
        _text(result[field], code, field, required=field == "message")
    choices = {
        "recipient_mode": {"selected", "all", "present", "absent", "nearest"},
        "delivery": {"immediate", "when_available"},
        "priority": {"quiet", "normal", "important", "critical"},
        "cycle_mode": {"update", "new"},
        "voice_mode": {"explicit", "occupied"},
    }
    for field, allowed in choices.items():
        _choice(result[field], allowed, code, field)
    channels = _list(result["channels"], code, "channels")
    if not channels:
        _fail(code, "channels", "select at least one channel")
    result["channels"] = list(
        dict.fromkeys(
            _choice(channel, {"mobile", "voice", "persistent"}, code, "channels")
            for channel in channels
        )
    )
    for field, domain in (
        ("person_entity_ids", "person"),
        ("notify_entity_ids", "notify"),
        ("media_player_entity_ids", "media_player"),
    ):
        result[field] = _entities(result[field], {domain}, code, field)
    result["mobile_device_ids"] = list(
        dict.fromkeys(
            _text(item, code, "mobile_device_ids", required=True)
            for item in _list(result["mobile_device_ids"], code, "mobile_device_ids")
        )
    )
    for field in ("respect_sleep", "resolve_on_clear"):
        _boolean(result[field], code, field)
    for field in ("expires_in", "timeout"):
        result[field] = _number(result[field], code, field)
    if result["volume"] is not None:
        result["volume"] = _number(result["volume"], code, "volume", maximum=100)
    for field, domain in (("camera_entity_id", "camera"), ("tts_entity_id", "tts")):
        _entity(result[field], {domain}, code, field, optional=True)
    _url(result["image_url"], code, "image_url", image=True)
    _url(result["click_url"], code, "click_url")

    buttons = []
    seen_buttons: set[str] = set()
    for index, raw in enumerate(_list(result["buttons"], code, "buttons")):
        field = f"buttons[{index}]"
        button = {"uri": "", "actions": [], "resolve": False}
        button.update(_mapping(raw, _BUTTON_KEYS, code, field))
        button_id = _text(button.get("id"), code, f"{field}.id", required=True)
        if not _SLUG.fullmatch(button_id):
            _fail(code, f"{field}.id", "must use letters, digits, _ or -")
        if button_id in seen_buttons:
            _fail(code, field, "button id must be unique")
        seen_buttons.add(button_id)
        _text(button.get("label"), code, f"{field}.label", required=True)
        _url(button["uri"], code, f"{field}.uri")
        _boolean(button["resolve"], code, f"{field}.resolve")
        for action_index, action in enumerate(
            _list(button["actions"], code, f"{field}.actions")
        ):
            action_field = f"{field}.actions[{action_index}]"
            if not isinstance(action, dict) or not action:
                _fail(code, action_field, "each action must be a nonempty object")
            _json(action, code, action_field)
        if button["uri"] and (button["actions"] or button["resolve"]):
            _fail(code, field, "a URI cannot combine actions or automatic resolution")
        buttons.append(button)
    result["buttons"] = buttons
    return result
