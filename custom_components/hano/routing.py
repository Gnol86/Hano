"""Pure routing decisions from a snapshot of Home Assistant states."""

import math
from typing import Any

_UNKNOWN = {"", "unknown", "unavailable", "none"}
_EARTH_RADIUS_METERS = 6_371_008.8


def _state(states: dict, entity_id: str) -> str:
    value = states.get(entity_id, {})
    state = value.get("state") if isinstance(value, dict) else None
    return state if isinstance(state, str) else "unknown"


def _sleep_reason(sensor: str, states: dict) -> str:
    if not sensor:
        return ""
    state = _state(states, sensor)
    if state == "off":
        return ""
    return "sleeping" if state == "on" else "unknown_sleep"


def _coordinate(value: Any, limit: float) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and -limit <= value <= limit
        and math.isfinite(value)
    )


def _distance(person_id: str, states: dict, home: tuple) -> tuple[float | None, str]:
    state = _state(states, person_id)
    if state == "home":
        return 0.0, ""
    if state.lower() in _UNKNOWN:
        return None, "unknown_presence"
    person_state = states.get(person_id, {})
    attributes = person_state.get("attributes", {})
    if not isinstance(attributes, dict):
        attributes = {}
    latitude, longitude = attributes.get("latitude"), attributes.get("longitude")
    if latitude is None or longitude is None:
        return None, "missing_position"
    if not _coordinate(latitude, 90) or not _coordinate(longitude, 180):
        return None, "invalid_position"
    if len(home) != 2 or not _coordinate(home[0], 90) or not _coordinate(home[1], 180):
        return None, "invalid_home_position"
    lat1, lon1, lat2, lon2 = map(math.radians, (*home, latitude, longitude))
    haversine = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    distance = (
        2 * _EARTH_RADIUS_METERS * math.asin(math.sqrt(min(1, max(0, haversine))))
    )
    return distance, ""


def _voice(request: dict, config: dict, states: dict) -> tuple[list[str], list[dict]]:
    if "voice" not in request["channels"]:
        return [], []
    players: list[str] = []
    reasons = []
    rooms = config["rooms"]
    if request["voice_mode"] == "explicit":
        for player in request["media_player_entity_ids"]:
            blockers = [
                _sleep_reason(room["sleep_entity_id"], states)
                for room in rooms
                if request["respect_sleep"]
                and player in room["media_player_entity_ids"]
            ]
            blocker = next((reason for reason in blockers if reason), "")
            if blocker:
                reasons.append({"target": player, "reason": f"room_{blocker}"})
            else:
                players.append(player)
    else:
        for room in rooms:
            occupancy = _state(states, room["presence_entity_id"])
            reason = ""
            if occupancy != "on":
                reason = (
                    "room_unoccupied" if occupancy == "off" else "unknown_occupancy"
                )
            elif request["respect_sleep"]:
                blocker = _sleep_reason(room["sleep_entity_id"], states)
                if blocker:
                    reason = f"room_{blocker}"
            if reason:
                reasons.append({"target": room["id"], "reason": reason})
            else:
                players.extend(room["media_player_entity_ids"])
        # A player shared with a sleeping room must not be announced elsewhere.
        if request["respect_sleep"]:
            for room in rooms:
                blocker = _sleep_reason(room["sleep_entity_id"], states)
                if blocker:
                    for player in room["media_player_entity_ids"]:
                        if player in players:
                            players = [item for item in players if item != player]
                            reasons.append(
                                {"target": player, "reason": f"room_{blocker}"}
                            )
    return list(dict.fromkeys(players)), reasons


def route(request: dict, config: dict, states: dict, home: tuple) -> dict[str, list]:
    """Route normalized inputs, with meter distances and one-meter nearest ties.

    Selected/all modes have no location requirement. Present/absent modes wait
    for the requested state; nearest considers the closest eligible people.
    Delivery policy is intentionally left to the lifecycle manager.
    """
    people = []
    mode = request["recipient_mode"]
    selected = set(request["person_entity_ids"])
    if "mobile" in request["channels"]:
        for person in config["persons"]:
            person_id = person["person_id"]
            if (mode == "selected" or selected) and person_id not in selected:
                continue
            state = _state(states, person_id)
            distance = None
            reason = ""
            if mode in {"present", "absent"}:
                if state.lower() in _UNKNOWN:
                    reason = "unknown_presence"
                elif mode == "present" and state != "home":
                    reason = "not_home"
                elif mode == "absent" and state == "home":
                    reason = "home"
            elif mode == "nearest":
                distance, reason = _distance(person_id, states, home)
            if not reason and request["respect_sleep"]:
                reason = _sleep_reason(person["sleep_entity_id"], states)
            people.append(
                {
                    "person_id": person_id,
                    "eligible": not reason,
                    "reason": reason or "eligible",
                    "distance": distance,
                }
            )
        if mode == "nearest":
            distances = [person["distance"] for person in people if person["eligible"]]
            if distances:
                closest = min(distances)
                for person in people:
                    if person["eligible"] and not math.isclose(
                        person["distance"], closest, abs_tol=1.0, rel_tol=1e-9
                    ):
                        person.update(eligible=False, reason="not_nearest")
    players, reasons = _voice(request, config, states)
    return {"persons": people, "media_player_entity_ids": players, "reasons": reasons}
