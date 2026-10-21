"""Native notification actions with validation and administrator permissions."""

import probatio
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError, Unauthorized

from .const import DOMAIN
from .errors import HanoError
from .models import normalize_request


def _request(value: dict) -> dict:
    try:
        return normalize_request(value)
    except HanoError as err:
        raise probatio.Invalid(str(err)) from err


REQUEST_SCHEMA = probatio.All(dict, _request)
RESOLVE_SCHEMA = probatio.Schema(
    {probatio.Required("notification_id"): probatio.All(str, probatio.Length(min=1))}
)


def get_manager(hass: HomeAssistant):
    """Resolve the currently loaded manager, including after entry reload."""
    if (manager := hass.data.get(DOMAIN, {}).get("manager")) is None:
        raise HanoError("not_loaded", "Configure Hano before using its actions")
    return manager


async def async_check_admin(hass: HomeAssistant, context) -> None:
    """Permit automation contexts; require an administrator for manual calls."""
    if context.user_id is not None:
        user = await hass.auth.async_get_user(context.user_id)
        if user is None or not user.is_active or not user.is_admin:
            raise Unauthorized(context=context)


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register once at integration setup, before config entries become available."""

    async def handle(call: ServiceCall) -> dict | None:
        await async_check_admin(hass, call.context)
        try:
            manager = get_manager(hass)
            if call.service == "resolve":
                result = await manager.resolve(
                    call.data["notification_id"], context=call.context
                )
            elif call.service == "preview":
                result = await manager.preview(dict(call.data), context=call.context)
            else:
                result = await manager.send(dict(call.data), context=call.context)
        except HanoError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="operation_failed",
                translation_placeholders={"detail": str(err), "code": err.code},
            ) from err
        return result if call.return_response else None

    for action, schema, response in (
        ("send", REQUEST_SCHEMA, SupportsResponse.OPTIONAL),
        ("resolve", RESOLVE_SCHEMA, SupportsResponse.OPTIONAL),
        ("preview", REQUEST_SCHEMA, SupportsResponse.ONLY),
    ):
        hass.services.async_register(
            DOMAIN, action, handle, schema=schema, supports_response=response
        )
