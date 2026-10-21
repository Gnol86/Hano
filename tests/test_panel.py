"""Administrator panel registration and deterministic content-hash cache busting."""

import asyncio
from hashlib import sha256
from unittest.mock import patch

import pytest
from homeassistant.components import frontend

from custom_components.hano import panel


@pytest.fixture
def installed_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "hano-panel.js"
    bundle.write_text(
        "customElements.define('hano-panel', class extends HTMLElement {});"
    )
    monkeypatch.setattr(panel, "FRONTEND_PATH", tmp_path)
    return bundle


def module_url(hass):
    return hass.data[frontend.DATA_PANELS]["hano"].config["_panel_custom"]["module_url"]


@pytest.mark.usefixtures("installed_bundle")
async def test_panel_admin_only_and_bundle_is_served(hass, hano_entry, hass_client):
    registered = hass.data[frontend.DATA_PANELS]["hano"]
    assert registered.require_admin is True
    content = (panel.FRONTEND_PATH / "hano-panel.js").read_bytes()
    url = module_url(hass)
    assert url == f"/hano_frontend/hano-panel.js?v={sha256(content).hexdigest()}"
    client = await hass_client()
    response = await client.get(url)
    assert response.status == 200
    assert await response.read() == content


@pytest.mark.usefixtures("installed_bundle")
async def test_reload_keeps_static_registration_but_hashes_current_bytes(
    hass, hano_entry
):
    old_url = module_url(hass)
    with patch.object(hass.http, "async_register_static_paths") as static:
        assert await hass.config_entries.async_reload(hano_entry.entry_id)
        static.assert_not_called()
    assert module_url(hass) == old_url
    (panel.FRONTEND_PATH / "hano-panel.js").write_text("/* updated Hano bundle */")
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    assert module_url(hass) != old_url


@pytest.mark.usefixtures("installed_bundle")
async def test_hash_calculation_is_outside_event_loop(hass, hano_entry, monkeypatch):
    original = panel._bundle_digest
    calls = []

    def digest():
        with pytest.raises(RuntimeError, match="no running event loop"):
            asyncio.get_running_loop()
        calls.append(True)
        return original()

    monkeypatch.setattr(panel, "_bundle_digest", digest)
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    assert calls == [True]


async def test_missing_panel_does_not_stop_engine(
    hass, installed_bundle, hano_entry, caplog
):
    installed_bundle.unlink()
    assert await hass.config_entries.async_reload(hano_entry.entry_id)
    assert module_url(hass) == "/hano_frontend/hano-panel.js"
    assert "Unable to read the panel bundle" in caplog.text
    assert await hass.config_entries.async_unload(hano_entry.entry_id)
    assert "hano" not in hass.data[frontend.DATA_PANELS]
