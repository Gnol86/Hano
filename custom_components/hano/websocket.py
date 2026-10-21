"""Administrator-only WebSocket API shared by the Hano panel and tests."""

import probatio
from homeassistant.components import websocket_api
from homeassistant.core import Context, callback
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .errors import HanoError
from .models import normalize_config, normalize_request
from .services import get_manager


async def handle(hass, connection, msg):
    """Authorize every operation, including snapshots and subscriptions."""
    try:
        if not connection.user.is_active or not connection.user.is_admin:
            raise Unauthorized()
        manager = get_manager(hass)
        context = Context(user_id=connection.user.id)
        kind = msg["type"]
        if kind == "hano/subscribe":

            @callback
            def publish(snapshot):
                if not connection.user.is_active or not connection.user.is_admin:
                    if unsubscribe := connection.subscriptions.pop(msg["id"], None):
                        unsubscribe()
                    return
                connection.send_event(msg["id"], snapshot)

            connection.subscriptions[msg["id"]] = async_dispatcher_connect(
                hass, "hano_snapshot", publish
            )
            connection.send_result(msg["id"])
            publish(manager.snapshot())
            return
        if kind == "hano/save":
            result = await manager.save(
                normalize_config(msg["config"]), msg["revision"], context=context
            )
        elif kind == "hano/validate":
            result = {"config": normalize_config(msg["config"])}
        elif kind == "hano/preview":
            result = await manager.preview(
                normalize_request(msg["request"]), context=context
            )
        elif kind == "hano/send":
            result = await manager.send(
                normalize_request(msg["request"]), context=context
            )
        elif kind == "hano/resolve":
            result = await manager.resolve(msg["notification_id"], context=context)
        elif kind == "hano/purge_history":
            result = await manager.purge_history(context=context)
        else:
            result = manager.snapshot()
        connection.send_result(msg["id"], result)
    except HanoError as err:
        connection.send_error(msg["id"], err.code, str(err))
    except Unauthorized:
        connection.send_error(
            msg["id"], "unauthorized", "Administrator access required"
        )
    except HomeAssistantError:
        connection.send_error(msg["id"], "command_failed", "Operation failed")


@callback
def async_register(hass):
    """Register native WebSocket schemas."""
    for kind, schema in {
        "hano/get": {},
        "hano/subscribe": {},
        "hano/save": {
            probatio.Required("config"): dict,
            probatio.Required("revision"): probatio.All(int, probatio.Range(min=0)),
        },
        "hano/validate": {probatio.Required("config"): dict},
        "hano/preview": {probatio.Required("request"): dict},
        "hano/send": {probatio.Required("request"): dict},
        "hano/resolve": {
            probatio.Required("notification_id"): probatio.All(
                str, probatio.Length(min=1)
            )
        },
        "hano/purge_history": {},
    }.items():
        handler = websocket_api.async_response(handle)
        handler = websocket_api.websocket_command(
            {probatio.Required("type"): kind, **schema}
        )(handler)
        websocket_api.async_register_command(hass, handler)
