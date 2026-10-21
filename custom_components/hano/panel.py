"""Register the local, administrator-only Hano sidebar panel."""

import logging
from hashlib import sha256
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, NAME

FRONTEND_PATH = Path(__file__).parent / "frontend"
_LOGGER = logging.getLogger(__name__)


def _bundle_digest() -> str:
    """Identify actual bundle contents even when versions or timestamps match."""
    return sha256((FRONTEND_PATH / "hano-panel.js").read_bytes()).hexdigest()


async def async_register_panel(hass: HomeAssistant) -> None:
    """Serve immutable code; all personal data travels through protected WebSocket."""
    module_url = "/hano_frontend/hano-panel.js"
    try:
        digest = await hass.async_add_executor_job(_bundle_digest)
    except OSError as err:
        _LOGGER.warning(
            "Unable to read the panel bundle for cache invalidation: %s", err
        )
    else:
        module_url = f"{module_url}?v={digest}"
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get("static_registered"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig("/hano_frontend", str(FRONTEND_PATH), False)]
        )
        data["static_registered"] = True
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=DOMAIN,
        webcomponent_name="hano-panel",
        sidebar_title=NAME,
        sidebar_icon="mdi:bell-ring-outline",
        module_url=module_url,
        require_admin=True,
        config_panel_domain=DOMAIN,
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove only the Hano sidebar entry."""
    frontend.async_remove_panel(hass, DOMAIN)
