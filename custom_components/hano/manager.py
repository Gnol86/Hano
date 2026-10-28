"""Durable notification lifecycle, per-destination dispatch and global resolution."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
from uuid import uuid4

from homeassistant.components import persistent_notification
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Context, Event, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.script import Script, async_validate_actions_config
from homeassistant.util import dt as dt_util

from .adapters import (
    Adapters,
    mobile_catalog,
    mobile_endpoint,
    mobile_tag,
    resolve_endpoint,
    validate_endpoint,
)
from .const import DOMAIN, STORAGE_VERSION, VERSION
from .errors import HanoError
from .models import default_config, normalize_config, normalize_request
from .reminders import next_reminder, reminder_due
from .routing import route
from .storage import StrictStore

_LOGGER = logging.getLogger(__name__)
_TOPOLOGY = (
    "recipient_mode",
    "person_entity_ids",
    "notify_entity_ids",
    "mobile_device_ids",
    "channels",
    "voice_mode",
    "media_player_entity_ids",
)
_TERMINAL = {"resolved", "expired"}


def now() -> str:
    return dt_util.utcnow().isoformat()


def _public_record(record: dict) -> dict:
    result = {k: deepcopy(v) for k, v in record.items() if not k.startswith("_")}
    result["deliveries"] = [
        {k: deepcopy(v) for k, v in item.items() if not k.startswith("_")}
        for item in record["deliveries"].values()
    ]
    return result


class HanoManager:
    """Persist intent before effects and close the cycle before clearing devices."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.hass, self.entry = hass, entry
        self.config = default_config()
        self.revision = 0
        self.notifications: dict[str, dict] = {}
        self._archive: list[dict] = []
        self._store = StrictStore(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}", atomic_writes=True
        )
        self._lock = asyncio.Lock()
        self._commands = asyncio.Lock()
        self._send_locks: dict[str, asyncio.Lock] = {}
        self._transition_locks: dict[str, asyncio.Lock] = {}
        self._listeners: set[Callable] = set()
        self._unsubs: list[Callable] = []
        self._tasks: set[asyncio.Task] = set()
        self._scripts: set[Script] = set()
        self._script_cycles: dict[Script, tuple[str, str]] = {}
        self._script_contexts: dict[Script, str] = {}
        self._stopped = False
        self._reevaluation: asyncio.Task | None = None
        self._dirty = False
        self._adapters = Adapters(hass)

    async def _authorize(self, context: Context | None) -> None:
        if context and context.user_id:
            user = await self.hass.auth.async_get_user(context.user_id)
            if user is None or not user.is_active or not user.is_admin:
                raise HanoError("unauthorized", "Administrator access required")

    def _state(self) -> dict:
        return {
            "config": self.config,
            "revision": self.revision,
            "notifications": self.notifications,
            "archive": self._archive,
        }

    @asynccontextmanager
    async def _mutation(self, *, skip_unchanged: bool = False):
        async with self._lock:
            previous = deepcopy(self._state())
            try:
                yield
                if skip_unchanged and self._state() == previous:
                    return
                await self._store.async_save(self._state())
            except BaseException:
                self.config = previous["config"]
                self.revision = previous["revision"]
                self.notifications = previous["notifications"]
                self._archive = previous["archive"]
                raise
        self.notify()

    async def load(self) -> None:
        data = await self._store.async_load()
        if data:
            self.config = normalize_config(data["config"])
            self.revision = data.get("revision", 0)
            self.notifications = data.get("notifications", {})
            self._archive = data.get("archive", [])
        async with self._mutation():
            for record in self.notifications.values():
                for delivery in record["deliveries"].values():
                    # A restart never catches up or immediately replays reminders.
                    deadline = delivery.get("next_reminder_at")
                    if deadline:
                        future = next_reminder(
                            record["request"], delivery, dt_util.utcnow()
                        )
                        delivery["next_reminder_at"] = (
                            max(deadline, future) if future else None
                        )
                    if delivery["status"] in {"sending", "updating", "clearing"}:
                        delivery["status"] = "unknown"
                        delivery["reason"] = "interrupted"
                        delivery["next_reminder_at"] = None
                        self._history(record, "interrupted", delivery["target"])
                    elif (
                        delivery["channel"] == "voice"
                        and delivery["status"] == "pending"
                    ):
                        delivery.update(status="skipped", reason="restart_no_replay")
                        self._history(
                            record, "skipped", delivery["target"], "restart_no_replay"
                        )
                for key, state in record.get("_button_runs", {}).items():
                    if state == "running":
                        record["_button_runs"][key] = "unknown"
        self._unsubs = [
            self.hass.bus.async_listen(EVENT_STATE_CHANGED, self._state_changed),
            self.hass.bus.async_listen(
                "mobile_app_notification_action", self._mobile_action
            ),
            self.hass.bus.async_listen(
                "mobile_app_notification_cleared", self._mobile_cleared
            ),
            self.hass.bus.async_listen(
                "mobile_app_notification_received", self._mobile_received
            ),
            persistent_notification.async_register_callback(
                self.hass, self._persistent_changed
            ),
            async_track_time_interval(
                self.hass, self._maintenance, timedelta(seconds=30)
            ),
        ]
        await self._expire_and_purge()
        # Reconstruct HA cards without re-sending mobile or voice effects.
        for record in self.notifications.values():
            if (
                record["status"] == "active"
                and "persistent" in record["request"]["channels"]
            ):
                self._adapters.persistent(record["_tag"], record["request"])
        await self._reevaluate()

    async def stop(self) -> None:
        self._stopped = True
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        for script in list(self._scripts):
            await script.async_unload()
        # Direct action calls are owned by HA, so let their current transport finish.
        for lock in [*self._transition_locks.values(), *self._send_locks.values()]:
            async with lock:
                pass
        self._listeners.clear()

    def subscribe(self, listener: Callable) -> Callable:
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @callback
    def notify(self) -> None:
        if self._stopped:
            return
        snapshot = self.snapshot()
        for listener in tuple(self._listeners):
            listener(snapshot)
        async_dispatcher_send(self.hass, "hano_snapshot", snapshot)

    def _catalog(self) -> dict:
        domains = {
            "person",
            "binary_sensor",
            "input_boolean",
            "notify",
            "media_player",
            "tts",
        }
        entities = [
            {
                "entity_id": s.entity_id,
                "name": s.name,
                "state": s.state,
                "domain": s.domain,
                "attributes": {
                    "supported_features": s.attributes.get("supported_features", 0)
                },
            }
            for s in self.hass.states.async_all()
            if s.domain in domains
        ]
        mobiles = [
            {
                k: v
                for k, v in item.items()
                if k in {"device_id", "name", "platform", "service"}
            }
            for item in mobile_catalog(self.hass)
        ]
        areas = [
            {"area_id": a.id, "name": a.name}
            for a in ar.async_get(self.hass).async_list_areas()
        ]
        return {
            "entities": entities,
            "mobile_services": mobiles,
            "mobile_devices": mobiles,
            "areas": areas,
        }

    def snapshot(self) -> dict:
        records = list(self.notifications.values()) + self._archive
        return {
            "version": VERSION,
            "config": deepcopy(self.config),
            "revision": self.revision,
            "notifications": [
                _public_record(r)
                for r in sorted(records, key=lambda r: r["created_at"], reverse=True)
            ],
            "catalog": self._catalog(),
        }

    async def save(self, config: dict, revision: int, context: Context | None = None):
        await self._authorize(context)
        value = normalize_config(config)
        # Validate references on saving, while permitting unavailable existing entities.
        for person in value["persons"]:
            for entity_id in (person["person_id"], person["sleep_entity_id"]):
                if entity_id and self.hass.states.get(entity_id) is None:
                    raise HanoError("invalid_target", f"Unknown entity: {entity_id}")
            for device in person["devices"]:
                resolve_endpoint(self.hass, device)
        for room in value["rooms"]:
            for entity_id in [
                room["presence_entity_id"],
                room["sleep_entity_id"],
                *room["media_player_entity_ids"],
            ]:
                if entity_id and self.hass.states.get(entity_id) is None:
                    raise HanoError("invalid_target", f"Unknown entity: {entity_id}")
        if (
            value["tts_entity_id"]
            and self.hass.states.get(value["tts_entity_id"]) is None
        ):
            raise HanoError("invalid_target", "Unknown default TTS engine")
        async with self._mutation():
            if revision != self.revision:
                raise HanoError(
                    "conflict", "Configuration changed; reload before saving"
                )
            self.config = value
            self.revision += 1
        return self.snapshot()

    def _states(self) -> dict:
        return {
            s.entity_id: {"state": s.state, "attributes": dict(s.attributes)}
            for s in self.hass.states.async_all()
        }

    def _route(self, request: dict, config: dict) -> dict:
        return route(
            request,
            config,
            self._states(),
            (self.hass.config.latitude, self.hass.config.longitude),
        )

    async def _prepare(
        self, request: dict, config: dict
    ) -> tuple[dict, dict, list[dict]]:
        request = normalize_request(request)
        self._expiry(request)
        if request["buttons"] and "mobile" not in request["channels"]:
            raise HanoError("unsupported_options", "Buttons require a mobile channel")
        if (
            request["camera_entity_id"]
            and self.hass.states.get(request["camera_entity_id"]) is None
        ):
            raise HanoError("invalid_target", "Unknown camera entity")
        configured = {p["person_id"]: p for p in config["persons"]}
        if set(request["person_entity_ids"]) - configured.keys():
            raise HanoError("invalid_target", "Select configured people")
        decisions = self._route(request, config)
        endpoints: list[dict] = []
        if "mobile" in request["channels"]:
            for decision in decisions["persons"]:
                person = configured[decision["person_id"]]
                if not person["devices"]:
                    raise HanoError(
                        "invalid_target", f"No devices for {person['person_id']}"
                    )
                for device in person["devices"]:
                    endpoint = resolve_endpoint(self.hass, device)
                    validate_endpoint(self.hass, endpoint, request)
                    endpoints.append(
                        {"endpoint": endpoint, "person_id": person["person_id"]}
                    )
            for entity_id in request["notify_entity_ids"]:
                endpoint = resolve_endpoint(
                    self.hass,
                    {
                        "type": "notify",
                        "target": entity_id,
                        "platform": "generic",
                        "device_id": "",
                    },
                )
                validate_endpoint(self.hass, endpoint, request)
                endpoints.append({"endpoint": endpoint, "person_id": ""})
            catalogue = {x["device_id"]: x for x in mobile_catalog(self.hass)}
            for device_id in request["mobile_device_ids"]:
                if device_id not in catalogue:
                    raise HanoError(
                        "invalid_target", f"Unknown mobile device: {device_id}"
                    )
                endpoint = mobile_endpoint(catalogue[device_id])
                validate_endpoint(self.hass, endpoint, request)
                endpoints.append({"endpoint": endpoint, "person_id": ""})
            if not endpoints:
                raise HanoError(
                    "invalid_target", "Select at least one mobile recipient"
                )
        if "voice" in request["channels"]:
            if (
                request["voice_mode"] == "explicit"
                and not request["media_player_entity_ids"]
            ):
                raise HanoError("invalid_target", "Select at least one speaker")
            self._adapters.validate_voice(
                request, config, decisions["media_player_entity_ids"]
            )
        for button in request["buttons"]:
            if button["actions"]:
                try:
                    await async_validate_actions_config(
                        self.hass, cv.SCRIPT_SCHEMA(deepcopy(button["actions"]))
                    )
                except Exception as err:
                    raise HanoError(
                        "invalid_request", f"Invalid button actions: {button['id']}"
                    ) from err
        return request, decisions, endpoints

    def _expiry(self, request: dict) -> str | None:
        try:
            return (
                (
                    dt_util.utcnow() + timedelta(seconds=request["expires_in"])
                ).isoformat()
                if request["expires_in"]
                else None
            )
        except (OverflowError, ValueError) as err:
            raise HanoError(
                "invalid_request", "Expiration is outside the supported date range"
            ) from err

    async def preview(self, request: dict, context: Context | None = None) -> dict:
        await self._authorize(context)
        request = normalize_request(request)
        existing = self.notifications.get(request["notification_id"])
        config = self._request_config(request, existing)
        request, decisions, endpoints = await self._prepare(request, config)
        return {
            "preview": True,
            "request": request,
            "routing": decisions,
            "destinations": [
                {"target": p["endpoint"]["target"], "person_id": p["person_id"]}
                for p in endpoints
            ],
        }

    def _request_config(self, request: dict, existing: dict | None) -> dict:
        return deepcopy(
            existing["_config"]
            if existing
            and existing["status"] == "active"
            and request["cycle_mode"] == "update"
            else self.config
        )

    def _history(self, record: dict, event: str, target: str = "", detail: str = ""):
        record["updated_at"] = now()
        record["history"].append(
            {"at": now(), "event": event, "target": target, "detail": detail}
        )
        # Bound individual noisy cycles; active requests themselves are not purged.
        record["history"] = record["history"][-1000:]

    def _delivery(
        self, key: str, channel: str, target: str, person_id: str = "", **extra
    ) -> dict:
        return {
            "key": key,
            "person_id": person_id,
            "channel": channel,
            "target": target,
            "status": "pending",
            "reason": "",
            "updated_at": now(),
            **extra,
        }

    def _build(
        self,
        request: dict,
        decisions: dict,
        endpoints: list,
        context: Context,
        config: dict | None = None,
    ) -> dict:
        notification_id = request["notification_id"] or uuid4().hex
        request = request | {"notification_id": notification_id}
        cycle = uuid4().hex
        record = {
            "notification_id": notification_id,
            "cycle_id": cycle,
            "status": "active",
            "title": request["title"],
            "message": request["message"],
            "request": request,
            "created_at": now(),
            "updated_at": now(),
            "resolved_at": None,
            "expires_at": self._expiry(request),
            "deliveries": {},
            "history": [],
            "_config": deepcopy(self.config if config is None else config),
            "_creator_user_id": context.user_id,
            "_button_runs": {},
            "_tag": (
                f"hano_{self.entry.entry_id}_"
                f"{sha256(notification_id.encode()).hexdigest()[:24]}_{cycle}"
            ),
            "_nearest_selected": None,
        }
        for item in endpoints:
            endpoint, person = item["endpoint"], item["person_id"]
            key = f"mobile:{endpoint['type']}:{endpoint['target']}"
            if key not in record["deliveries"]:
                record["deliveries"][key] = self._delivery(
                    key,
                    "mobile",
                    endpoint["target"],
                    person,
                    _endpoint=endpoint,
                    _persons=[],
                    _tokens={},
                    _attempted=False,
                )
            record["deliveries"][key]["_persons"].append(person)
        if "voice" in request["channels"]:
            for player in decisions["media_player_entity_ids"]:
                key = f"voice:{player}"
                record["deliveries"][key] = self._delivery(key, "voice", player)
        if "persistent" in request["channels"]:
            record["deliveries"]["persistent"] = self._delivery(
                "persistent", "persistent", record["_tag"]
            )
        self._history(record, "created")
        for decision in decisions["reasons"]:
            self._history(record, "skipped", decision["target"], decision["reason"])
        return record

    async def send(self, request: dict, context: Context | None = None) -> dict:
        await self._authorize(context)
        context = context or Context()
        if self._stopped or self.hass.is_stopping:
            raise HanoError("unavailable", "Hano is unloading")
        async with self._commands:
            if self._stopped or self.hass.is_stopping:
                raise HanoError("unavailable", "Hano is unloading")
            request = normalize_request(request)
            identifier = request["notification_id"] or uuid4().hex
            request["notification_id"] = identifier
            transition = self._transition_locks.setdefault(identifier, asyncio.Lock())
            async with transition:
                previous = self.notifications.get(identifier)
                config = self._request_config(request, previous)
                request, decisions, endpoints = await self._prepare(request, config)
                update = bool(
                    previous
                    and previous["status"] == "active"
                    and request["cycle_mode"] == "update"
                )
                if not update and previous and previous["status"] == "active":
                    await self._resolve(identifier, context, "superseded")
                async with self._send_locks.setdefault(identifier, asyncio.Lock()):
                    if update:
                        if any(previous["request"][k] != request[k] for k in _TOPOLOGY):
                            raise HanoError(
                                "invalid_request",
                                "Changing recipients or channels requires a new cycle",
                            )
                        for delivery in previous["deliveries"].values():
                            if delivery["channel"] == "mobile":
                                validate_endpoint(
                                    self.hass, delivery["_endpoint"], request
                                )
                        async with self._mutation():
                            record = self.notifications[identifier]
                            record.update(
                                request=request,
                                title=request["title"],
                                message=request["message"],
                                expires_at=self._expiry(request),
                            )
                            for delivery in record["deliveries"].values():
                                if delivery["channel"] == "mobile":
                                    delivery["_tokens"] = {}
                                    delivery["next_reminder_at"] = (
                                        next_reminder(
                                            request, delivery, dt_util.utcnow()
                                        )
                                        if delivery["status"]
                                        in {"accepted", "received", "cleared"}
                                        else None
                                    )
                            self._history(record, "updated")
                    else:
                        record = self._build(
                            request, decisions, endpoints, context, config
                        )
                        async with self._mutation():
                            if previous:
                                self._archive.append(
                                    deepcopy(self.notifications[identifier])
                                )
                            self.notifications[identifier] = record
                    cycle = self.notifications[identifier]["cycle_id"]
            await self._dispatch(identifier, cycle, context, refresh=update)
            return _public_record(self.notifications[identifier])

    def _eligibility(
        self, record: dict, delivery: dict, decisions: dict
    ) -> tuple[bool, str]:
        if delivery["channel"] == "voice":
            return (
                delivery["target"] in decisions["media_player_entity_ids"],
                "voice_no_longer_eligible",
            )
        if delivery["channel"] != "mobile":
            return True, "eligible"
        owners = delivery["_persons"]
        if "" in owners:
            return True, "explicit_target"
        rows = {p["person_id"]: p for p in decisions["persons"]}
        nearest = record["_nearest_selected"]
        if nearest is not None and not set(owners).intersection(nearest):
            return False, "not_nearest"
        for owner in owners:
            if owner in rows and rows[owner]["eligible"]:
                return True, "eligible"
        return False, next(
            (rows[p]["reason"] for p in owners if p in rows), "unknown_recipient"
        )

    async def _dispatch(
        self,
        identifier: str,
        cycle: str,
        context: Context,
        refresh: bool = False,
        *,
        reminders: bool = False,
    ) -> None:
        lock = self._send_locks.setdefault(identifier, asyncio.Lock())
        async with lock:
            record = self.notifications.get(identifier)
            if (
                not record
                or record["cycle_id"] != cycle
                or record["status"] != "active"
                or self._stopped
                or self.hass.is_stopping
            ):
                return
            decisions = self._route(record["request"], record["_config"])
            if (
                record["request"]["recipient_mode"] == "nearest"
                and record["_nearest_selected"] is None
            ):
                chosen = [p["person_id"] for p in decisions["persons"] if p["eligible"]]
                if chosen:
                    async with self._mutation():
                        self.notifications[identifier]["_nearest_selected"] = chosen
            for key in list(record["deliveries"]):
                record = self.notifications[identifier]
                if (
                    record["status"] != "active"
                    or record["cycle_id"] != cycle
                    or self._stopped
                    or self.hass.is_stopping
                ):
                    break
                if (
                    record["expires_at"]
                    and dt_util.parse_datetime(record["expires_at"]) <= dt_util.utcnow()
                ):
                    self._spawn(
                        self.resolve(identifier, reason="expired", expected_cycle=cycle)
                    )
                    break
                delivery = record["deliveries"][key]
                if reminders and not reminder_due(
                    record["request"], delivery, dt_util.utcnow()
                ):
                    continue
                routing_request = record["request"]
                if record["_nearest_selected"] is not None:
                    routing_request = routing_request | {
                        "recipient_mode": "selected",
                        "person_entity_ids": record["_nearest_selected"],
                    }
                decisions = self._route(routing_request, record["_config"])
                updating = (
                    refresh
                    and delivery["status"] in {"accepted", "received"}
                    and delivery["channel"] != "voice"
                )
                if delivery["status"] != "pending" and not updating and not reminders:
                    continue
                # Refresh existing messages even if their owner went asleep.
                eligible, reason = (
                    (True, "updated")
                    if updating
                    else self._eligibility(record, delivery, decisions)
                )
                if not eligible:
                    async with self._mutation():
                        delivery = self.notifications[identifier]["deliveries"][key]
                        if reminders:
                            # Keep prior status and budget while asleep or away.
                            delivery["next_reminder_at"] = next_reminder(
                                record["request"], delivery, dt_util.utcnow()
                            )
                            self._history(
                                record, "reminder_deferred", delivery["target"], reason
                            )
                            continue
                        changed = delivery["reason"] != reason
                        delivery["reason"] = reason
                        if (
                            delivery["channel"] == "voice"
                            or record["request"]["delivery"] == "immediate"
                            or (
                                reason == "not_nearest"
                                and record["_nearest_selected"] is not None
                            )
                        ):
                            delivery["status"] = "skipped"
                        if changed:
                            self._history(
                                record, delivery["status"], delivery["target"], reason
                            )
                    continue
                async with self._mutation():
                    record = self.notifications[identifier]
                    delivery = record["deliveries"][key]
                    delivery["status"] = (
                        "updating" if updating or reminders else "sending"
                    )
                    delivery["updated_at"] = now()
                    delivery["_attempted"] = True
                    if reminders:
                        delivery["reminder_count"] = (
                            delivery.get("reminder_count", 0) + 1
                        )
                        delivery["next_reminder_at"] = None
                        self._history(record, "reminder_attempted", delivery["target"])
                    if delivery["channel"] == "mobile" and (
                        not reminders or not delivery["_tokens"]
                    ):
                        delivery["_tokens"] = {
                            b["id"]: f"HANO_{cycle}_{uuid4().hex}"
                            for b in record["request"]["buttons"]
                            if not b["uri"]
                        }
                    self._history(record, delivery["status"], delivery["target"])
                # Save intent before transport; resolution may close the cycle.
                if self.hass.is_stopping:
                    return
                if self.notifications[identifier]["status"] != "active":
                    break
                outcome, detail = "accepted", ""
                try:
                    async with asyncio.timeout(30):
                        if delivery["channel"] == "mobile":
                            await self._adapters.send_mobile(
                                delivery["_endpoint"],
                                record["request"],
                                record["_tag"],
                                delivery["_tokens"],
                                context,
                            )
                        elif delivery["channel"] == "voice":
                            await self._adapters.speak(
                                delivery["target"],
                                record["request"],
                                record["_config"],
                                context,
                            )
                        else:
                            self._adapters.persistent(record["_tag"], record["request"])
                except TimeoutError:
                    outcome, detail = "unknown", "transport_timeout"
                except asyncio.CancelledError:
                    raise
                except Exception as err:
                    outcome, detail = "failed", type(err).__name__
                    _LOGGER.warning(
                        "Notification transport failed for %s: %s",
                        delivery["target"],
                        type(err).__name__,
                    )
                async with self._mutation():
                    current = self.notifications.get(identifier)
                    if current is not None and current["cycle_id"] == cycle:
                        actual = current["deliveries"][key]
                        if actual["status"] not in {"received", "cleared"}:
                            actual.update(
                                status=outcome, reason=detail, updated_at=now()
                            )
                        if actual["channel"] == "mobile":
                            actual["next_reminder_at"] = (
                                next_reminder(
                                    current["request"], actual, dt_util.utcnow()
                                )
                                if outcome == "accepted"
                                and current["status"] == "active"
                                else None
                            )
                        self._history(current, outcome, actual["target"], detail)

    async def resolve(
        self,
        notification_id: str,
        context: Context | None = None,
        reason: str = "manual",
        *,
        expected_cycle: str | None = None,
    ) -> dict:
        await self._authorize(context)
        context = context or Context()
        async with self._transition_locks.setdefault(notification_id, asyncio.Lock()):
            return await self._resolve(notification_id, context, reason, expected_cycle)

    async def _resolve(
        self,
        notification_id: str,
        context: Context,
        reason: str,
        expected_cycle: str | None = None,
    ) -> dict:
        async with self._mutation(skip_unchanged=True):
            record = self.notifications.get(notification_id)
            if record is None:
                return {
                    "notification_id": notification_id,
                    "cycle_id": None,
                    "status": "not_found",
                    "changed": False,
                }
            if expected_cycle and record["cycle_id"] != expected_cycle:
                return {
                    "notification_id": notification_id,
                    "cycle_id": expected_cycle,
                    "status": "stale",
                }
            if record["status"] in _TERMINAL:
                return _public_record(record)
            record["status"] = "expired" if reason == "expired" else "resolved"
            record["resolved_at"] = now()
            cycle = record["cycle_id"]
            for delivery in record["deliveries"].values():
                delivery["next_reminder_at"] = None
                if delivery["status"] == "pending":
                    delivery.update(status="cancelled", reason=reason, updated_at=now())
            self._history(record, record["status"], detail=reason)
        for script, identity in list(self._script_cycles.items()):
            if (
                identity == (notification_id, cycle)
                and self._script_contexts.get(script) != context.id
            ):
                await script.async_stop()
        # Clear after in-flight sends, including their possibly late results.
        async with self._send_locks.setdefault(notification_id, asyncio.Lock()):
            record = self.notifications.get(notification_id)
            if record is None or record["cycle_id"] != cycle:
                return {
                    "notification_id": notification_id,
                    "cycle_id": cycle,
                    "status": "resolved",
                }
            self._adapters.dismiss_persistent(record["_tag"])
            for key, delivery in list(record["deliveries"].items()):
                if self._stopped or self.hass.is_stopping:
                    break
                if delivery["channel"] != "mobile" or not delivery.get("_attempted"):
                    continue
                async with self._mutation():
                    delivery["status"] = "clearing"
                outcome, detail = "clear_requested", ""
                try:
                    async with asyncio.timeout(30):
                        supported = await self._adapters.clear(
                            delivery["_endpoint"], record["_tag"], context
                        )
                    if not supported:
                        outcome, detail = "unsupported", "remote_clear_unsupported"
                except TimeoutError:
                    outcome, detail = "unknown", "clear_timeout"
                except Exception as err:
                    outcome, detail = "failed", type(err).__name__
                async with self._mutation():
                    actual = self.notifications[notification_id]["deliveries"][key]
                    if self.notifications[notification_id]["cycle_id"] != cycle:
                        break
                    if actual["status"] != "cleared":
                        actual.update(status=outcome, reason=detail, updated_at=now())
                    self._history(record, outcome, actual["target"], detail)
        return _public_record(record)

    def _spawn(self, coro) -> asyncio.Task | None:
        if self._stopped:
            coro.close()
            return None
        task = self.hass.async_create_task(coro, "hano event")
        self._tasks.add(task)
        task.add_done_callback(self._task_done)
        return task

    @callback
    def _task_done(self, task: asyncio.Task) -> None:
        self._tasks.discard(task)
        if not task.cancelled() and (error := task.exception()):
            _LOGGER.error(
                "Notification background operation failed: %s", type(error).__name__
            )

    @callback
    def _state_changed(self, event: Event) -> None:
        entity_id = event.data.get("entity_id", "")
        if not entity_id.startswith(("person.", "binary_sensor.", "input_boolean.")):
            return
        self._dirty = True
        if self._reevaluation is None or self._reevaluation.done():
            self._reevaluation = self._spawn(self._drain_changes())

    async def _drain_changes(self) -> None:
        while self._dirty and not self._stopped:
            self._dirty = False
            await self._reevaluate()

    async def _reevaluate(self) -> None:
        for record in list(self.notifications.values()):
            if record["status"] != "active":
                continue
            if (
                record["expires_at"]
                and dt_util.parse_datetime(record["expires_at"]) <= dt_util.utcnow()
            ):
                await self.resolve(
                    record["notification_id"],
                    reason="expired",
                    expected_cycle=record["cycle_id"],
                )
                continue
            if any(
                d["status"] == "pending" and d["channel"] == "mobile"
                for d in record["deliveries"].values()
            ):
                await self._dispatch(
                    record["notification_id"], record["cycle_id"], Context()
                )

    async def _maintenance(self, _time) -> None:
        await self._expire_and_purge()
        await self._reevaluate()
        for record in list(self.notifications.values()):
            if record["status"] == "active" and any(
                reminder_due(record["request"], delivery, dt_util.utcnow())
                for delivery in record["deliveries"].values()
            ):
                await self._dispatch(
                    record["notification_id"],
                    record["cycle_id"],
                    Context(),
                    reminders=True,
                )

    async def _expire_and_purge(self) -> None:
        for record in list(self.notifications.values()):
            if (
                record["status"] == "active"
                and record["expires_at"]
                and dt_util.parse_datetime(record["expires_at"]) <= dt_util.utcnow()
            ):
                await self.resolve(
                    record["notification_id"],
                    reason="expired",
                    expected_cycle=record["cycle_id"],
                )
        cutoff = dt_util.utcnow() - timedelta(days=self.config["history_days"])
        expired_ids = [
            key
            for key, r in self.notifications.items()
            if r["resolved_at"]
            and dt_util.parse_datetime(r["resolved_at"]) < cutoff
            and not self._transition_locks.get(key, asyncio.Lock()).locked()
        ]
        old_archive = [
            r
            for r in self._archive
            if dt_util.parse_datetime(r["resolved_at"] or r["updated_at"]) < cutoff
        ]
        if expired_ids or old_archive:
            async with self._mutation():
                for key in expired_ids:
                    self.notifications.pop(key, None)
                    self._send_locks.pop(key, None)
                self._archive = [r for r in self._archive if r not in old_archive]

    async def purge_history(self, context: Context | None = None):
        await self._authorize(context)
        async with self._mutation():
            self._archive.clear()
            self.notifications = {
                key: r
                for key, r in self.notifications.items()
                if r["status"] == "active"
                or self._transition_locks.get(key, asyncio.Lock()).locked()
            }
        return self.snapshot()

    @callback
    def _persistent_changed(self, update_type, notifications) -> None:
        if update_type != persistent_notification.UpdateType.REMOVED:
            return
        for record in list(self.notifications.values()):
            if record["status"] == "active" and record["_tag"] in notifications:
                self._spawn(
                    self.resolve(
                        record["notification_id"],
                        reason="removed_in_home_assistant",
                        expected_cycle=record["cycle_id"],
                    )
                )

    def _matches_device(self, delivery: dict, event: Event) -> bool:
        endpoint = delivery["_endpoint"]
        reported = event.data.get("device_id")
        if reported and reported not in {
            endpoint.get("device_id"),
            endpoint.get("app_device_id"),
        }:
            return False
        expected_user = endpoint.get("user_id")
        if expected_user and event.context.user_id != expected_user:
            return False
        if not reported and (
            not expected_user or event.context.user_id != expected_user
        ):
            return False
        return True

    @callback
    def _mobile_action(self, event: Event) -> None:
        action = event.data.get("action")
        if not isinstance(action, str) or not action.startswith("HANO_"):
            return
        self._spawn(self._handle_button(event))

    async def _handle_button(self, event: Event) -> None:
        action = event.data["action"]
        match = None
        for record in self.notifications.values():
            if record["status"] != "active":
                continue
            for delivery in record["deliveries"].values():
                if delivery["channel"] != "mobile" or not self._matches_device(
                    delivery, event
                ):
                    continue
                button_id = next(
                    (
                        k
                        for k, token in delivery.get("_tokens", {}).items()
                        if token == action
                    ),
                    None,
                )
                if button_id:
                    match = (
                        record["notification_id"],
                        record["cycle_id"],
                        button_id,
                        delivery["key"],
                    )
                    break
        if match is None:
            return
        identifier, cycle, button_id, key = match
        async with self._mutation():
            record = self.notifications[identifier]
            if (
                record["status"] != "active"
                or record["cycle_id"] != cycle
                or button_id in record["_button_runs"]
                or record["deliveries"][key].get("_tokens", {}).get(button_id) != action
            ):
                return
            button = next(
                (b for b in record["request"]["buttons"] if b["id"] == button_id), None
            )
            if not button:
                return
            record["_button_runs"][button_id] = "running"
            self._history(
                record,
                "button_received",
                record["deliveries"][key]["target"],
                button_id,
            )
            creator = record["_creator_user_id"]
        # Execute with the authority of the automation or action author.
        context = Context(user_id=creator, parent_id=event.context.id)
        script = None
        success = False
        try:
            await self._authorize(context)
            if button["actions"]:
                sequence = await async_validate_actions_config(
                    self.hass, cv.SCRIPT_SCHEMA(deepcopy(button["actions"]))
                )
                script = Script(self.hass, sequence, f"Hano {button_id}", DOMAIN)
                self._scripts.add(script)
                self._script_cycles[script] = (identifier, cycle)
                self._script_contexts[script] = context.id
                current = self.notifications.get(identifier)
                if (
                    not current
                    or current["cycle_id"] != cycle
                    or current["status"] != "active"
                ):
                    return
                result = await script.async_run(
                    {
                        "notification_id": identifier,
                        "cycle_id": cycle,
                        "button_id": button_id,
                    },
                    context=context,
                )
                success = result is not None
            else:
                success = True
        except Exception as err:
            _LOGGER.warning("Notification button failed: %s", type(err).__name__)
        finally:
            if script:
                await script.async_unload()
                self._scripts.discard(script)
                self._script_cycles.pop(script, None)
                self._script_contexts.pop(script, None)
        async with self._mutation():
            record = self.notifications.get(identifier)
            if not record or record["cycle_id"] != cycle:
                return
            record["_button_runs"][button_id] = "completed" if success else "failed"
            self._history(
                record,
                "button_completed" if success else "button_failed",
                detail=button_id,
            )
        self.hass.bus.async_fire(
            "hano_notification_action",
            {
                "notification_id": identifier,
                "cycle_id": cycle,
                "button_id": button_id,
                "success": success,
            },
            context=context,
        )
        if success and button["resolve"] and record["status"] == "active":
            await self.resolve(
                identifier, context=context, reason="button", expected_cycle=cycle
            )

    @callback
    def _mobile_cleared(self, event: Event) -> None:
        self._spawn(self._handle_mobile_status(event, "cleared"))

    @callback
    def _mobile_received(self, event: Event) -> None:
        self._spawn(self._handle_mobile_status(event, "received"))

    async def _handle_mobile_status(self, event: Event, status: str) -> None:
        tag = event.data.get("tag")
        if not tag:
            return
        for record in list(self.notifications.values()):
            if tag not in {record["_tag"], mobile_tag(record["_tag"], "ios")}:
                continue
            if status == "received" and record["status"] != "active":
                return
            matched = [
                d
                for d in record["deliveries"].values()
                if d["channel"] == "mobile"
                and d.get("_attempted")
                and self._matches_device(d, event)
            ]
            # A tag alone does not identify which of multiple recipients sent an event.
            if not event.data.get("device_id") and not event.context.user_id:
                return
            if not matched:
                return
            if not event.data.get("device_id") and len(matched) != 1:
                return
            matched = [
                d
                for d in matched
                if mobile_tag(record["_tag"], d["_endpoint"].get("platform", "")) == tag
            ]
            if not matched:
                return
            async with self._mutation():
                for delivery in matched:
                    if delivery["status"] == status:
                        continue
                    if status == "received" and delivery["status"] in {
                        "cleared",
                        "clear_requested",
                        "clearing",
                    }:
                        continue
                    delivery.update(status=status, updated_at=now())
                    self._history(record, status, delivery["target"])
            if (
                status == "cleared"
                and record["status"] == "active"
                and record["request"]["resolve_on_clear"]
            ):
                await self.resolve(
                    record["notification_id"],
                    reason="mobile_clear",
                    expected_cycle=record["cycle_id"],
                )
