"""Capability-aware transports. A successful call is not proof of delivery."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.components.notify import NotifyEntityFeature
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .errors import HanoError


def mobile_catalog(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Return only non-secret registration metadata and registered services."""
    registry = dr.async_get(hass)
    output = []
    for entry in hass.config_entries.async_entries("mobile_app"):
        name = entry.data.get("device_name", entry.title)
        service = f"notify.{slugify(f'mobile_app_{name}')}"
        if not hass.services.has_service(*service.split(".", 1)):
            continue
        device = registry.async_get_device_by_identifier(
            ("mobile_app", entry.data.get("device_id", "")), entry.entry_id
        )
        if device is None:
            continue
        platform = "ios" if entry.data.get("manufacturer") == "Apple" else "android"
        output.append(
            {
                "device_id": device.id,
                "app_device_id": entry.data.get("device_id", ""),
                "entry_id": entry.entry_id,
                "user_id": entry.data.get("user_id"),
                "name": name,
                "platform": platform,
                "service": service,
            }
        )
    return output


def mobile_endpoint(item: dict[str, Any]) -> dict[str, Any]:
    """Freeze registration identity for a cycle, without credentials."""
    return {
        "type": "mobile",
        "target": item["service"],
        "platform": item["platform"],
        "device_id": item["device_id"],
        "app_device_id": item.get("app_device_id", ""),
        "user_id": item.get("user_id"),
    }


def resolve_endpoint(hass: HomeAssistant, value: dict[str, Any]) -> dict[str, Any]:
    """Resolve a configured destination, upgrading Companion notify entities."""
    result = deepcopy(value)
    target = result["target"]
    entries = mobile_catalog(hass)
    if result["type"] == "notify":
        entity = er.async_get(hass).async_get(target)
        if entity and entity.platform == "mobile_app":
            match = next(
                (x for x in entries if x["entry_id"] == entity.config_entry_id), None
            )
            if match is None:
                raise HanoError("invalid_target", f"No mobile service for {target}")
            return mobile_endpoint(match)
        if hass.states.get(target) is None:
            raise HanoError("invalid_target", f"Unknown notification entity: {target}")
        return result
    if not hass.services.has_service(*target.split(".", 1)):
        raise HanoError("invalid_target", f"Unknown mobile service: {target}")
    # Never permit an arbitrary service to acquire mobile transport privileges.
    if not target.startswith("notify.mobile_app_"):
        raise HanoError("invalid_target", "Expected a Companion mobile_app service")
    match = next((x for x in entries if x["service"] == target), None)
    if match:
        if result.get("device_id") and result["device_id"] not in {
            match["device_id"],
            match["app_device_id"],
        }:
            raise HanoError("invalid_target", f"Device/service mismatch: {target}")
        return mobile_endpoint(match)
    # Useful for development/test integrations; UI normally selects a discovery row.
    return result


def validate_endpoint(hass: HomeAssistant, endpoint: dict, request: dict) -> None:
    """Reject unsupported combinations before any destination is contacted."""
    if endpoint["type"] == "mobile":
        platform = endpoint["platform"]
        if platform not in {"ios", "android"}:
            raise HanoError("unsupported_options", "Select the Companion platform")
        if platform == "ios" and request["timeout"]:
            raise HanoError(
                "unsupported_options", "Notification timeout requires Android"
            )
        if platform == "ios" and (
            (request["icon"] and not request["title"])
            or (request["color"] and not request["icon"])
        ):
            raise HanoError(
                "unsupported_options",
                "An iOS icon requires a title; its color requires an icon",
            )
        if request["camera_entity_id"] and request["image_url"]:
            raise HanoError("unsupported_options", "Choose either a camera or an image")
        if platform == "android" and len(request["buttons"]) > 3:
            raise HanoError(
                "unsupported_options", "Android supports at most three buttons"
            )
        if request["buttons"] and not endpoint.get("device_id"):
            raise HanoError(
                "invalid_target", "Buttons need an identified mobile device"
            )
        return
    rich = (
        request["buttons"]
        or request["image_url"]
        or request["click_url"]
        or request["camera_entity_id"]
        or request["icon"]
        or request["color"]
        or request["timeout"]
        or request["priority"] != "normal"
        or request["resolve_on_clear"]
    )
    if rich:
        raise HanoError(
            "unsupported_options",
            f"{endpoint['target']} only supports a message and optional title",
        )
    state = hass.states.get(endpoint["target"])
    if (
        request["title"]
        and state
        and not (
            state.attributes.get("supported_features", 0) & NotifyEntityFeature.TITLE
        )
    ):
        raise HanoError(
            "unsupported_options", f"Title not supported: {state.entity_id}"
        )


def mobile_tag(tag: str, platform: str) -> str:
    """Keep iOS collapse IDs within APNs' 64-byte limit, including stored cycles.

    Hash the complete identity so updates and clears share a tag without merging
    distinct cycles. Android and HA persistent notification identities stay intact.
    """
    if platform == "ios" and len(tag.encode("utf-8")) > 64:
        return sha256(tag.encode("utf-8")).hexdigest()
    return tag


def mobile_payload(
    request: dict, tag: str, tokens: dict[str, str], platform: str
) -> dict:
    """Translate common options explicitly, preserving platform differences."""
    data: dict[str, Any] = {"tag": mobile_tag(tag, platform)}
    priority = request["priority"]
    if platform == "ios":
        levels = {
            "quiet": "passive",
            "normal": "active",
            "important": "time-sensitive",
            "critical": "critical",
        }
        data["push"] = {"interruption-level": levels[priority]}
        if priority == "critical":
            data["push"]["sound"] = {"name": "default", "critical": 1, "volume": 1.0}
    elif priority in ("important", "critical"):
        data.update(ttl=0, priority="high")
        if priority == "critical":
            data["channel"] = "alarm_stream"
    elif priority == "quiet":
        data["channel"] = "Hano silent"
        data["importance"] = "min"
    for source, destination in (
        ("image_url", "image"),
        ("icon", "notification_icon"),
        ("color", "color"),
    ):
        if request[source]:
            data[destination] = request[source]
    if request["click_url"]:
        data.update(url=request["click_url"], clickAction=request["click_url"])
    if request["camera_entity_id"]:
        if platform == "ios":
            data["entity_id"] = request["camera_entity_id"]
        else:
            data["image"] = f"/api/camera_proxy/{request['camera_entity_id']}"
    if request["timeout"]:
        data["timeout"] = request["timeout"]
    if request["buttons"]:
        data["actions"] = [
            {"action": "URI", "title": b["label"], "uri": b["uri"]}
            if b["uri"]
            else {"action": tokens[b["id"]], "title": b["label"]}
            for b in request["buttons"]
        ]
    if platform == "android":
        data["confirmation"] = True
    return {"message": request["message"], "title": request["title"], "data": data}


class Adapters:
    """Use existing Home Assistant integrations; do not call vendor APIs."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    def validate_voice(self, request: dict, config: dict, players: list[str]) -> None:
        engine = request["tts_entity_id"] or config["tts_entity_id"]
        if not engine or self.hass.states.get(engine) is None:
            raise HanoError("invalid_target", "Select an existing TTS entity")
        if not self.hass.services.has_service("tts", "speak"):
            raise HanoError("invalid_target", "TTS is not available")
        registry = er.async_get(self.hass)
        for player in players:
            if self.hass.states.get(player) is None:
                raise HanoError("invalid_target", f"Unknown media player: {player}")
            if request["volume"] is not None:
                entity = registry.async_get(player)
                if (
                    player not in config["native_volume_entity_ids"]
                    or entity is None
                    or entity.platform != "sonos"
                ):
                    raise HanoError(
                        "unsupported_volume",
                        f"Native volume has not been verified for {player}",
                    )

    async def send_mobile(
        self, endpoint: dict, request: dict, tag: str, tokens: dict, context: Context
    ) -> None:
        if endpoint["type"] == "mobile":
            payload = mobile_payload(request, tag, tokens, endpoint["platform"])
            domain, service = endpoint["target"].split(".", 1)
        else:
            state = self.hass.states.get(endpoint["target"])
            if state is None or state.state == "unavailable":
                raise HanoError("unavailable", endpoint["target"])
            domain, service = "notify", "send_message"
            payload = {"entity_id": endpoint["target"], "message": request["message"]}
            if request["title"]:
                payload["title"] = request["title"]
        await self.hass.services.async_call(
            domain, service, payload, blocking=True, context=context
        )

    async def clear(self, endpoint: dict, tag: str, context: Context) -> bool:
        if endpoint["type"] != "mobile":
            return False
        await self.hass.services.async_call(
            *endpoint["target"].split(".", 1),
            {
                "message": "clear_notification",
                "data": {"tag": mobile_tag(tag, endpoint["platform"])},
            },
            blocking=True,
            context=context,
        )
        return True

    async def speak(self, player: str, request: dict, config: dict, context: Context):
        state = self.hass.states.get(player)
        if state is None or state.state in {"unknown", "unavailable"}:
            raise HanoError("unavailable", player)
        engine = request["tts_entity_id"] or config["tts_entity_id"]
        language = request["tts_language"] or config["tts_language"]
        message = request["voice_message"] or request["message"]
        if request["volume"] is None:
            data = {
                "entity_id": engine,
                "media_player_entity_id": player,
                "message": message,
            }
            if language:
                data["language"] = language
            await self.hass.services.async_call(
                "tts", "speak", data, blocking=True, context=context
            )
        else:
            self.validate_voice(request, config, [player])
            from homeassistant.components import tts  # noqa: PLC0415

            media_id = tts.generate_media_source_id(
                self.hass, message, engine=engine, language=language or None
            )
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": player,
                    "media_content_id": media_id,
                    "media_content_type": "music",
                    "announce": True,
                    "extra": {"volume": request["volume"]},
                },
                blocking=True,
                context=context,
            )

    def persistent(self, tag: str, request: dict) -> None:
        message = request["message"]
        if request["image_url"]:
            message += f"\n\n![image]({request['image_url']})"
        persistent_notification.async_create(
            self.hass, message, request["title"] or None, tag
        )

    def dismiss_persistent(self, tag: str) -> None:
        persistent_notification.async_dismiss(self.hass, tag)
