"""Discover Hano and load real isolated Home Assistant entries."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture(autouse=True)
def enable_hano(enable_custom_integrations):
    """Enable custom component discovery for each Home Assistant instance."""


@pytest.fixture
async def hano_entry(hass):
    """Load the actual integration with no household devices or network calls."""
    entry = MockConfigEntry(domain="hano", title="Hano", unique_id="hano", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield entry
    if hass.data.get("hano", {}).get("manager"):
        await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
