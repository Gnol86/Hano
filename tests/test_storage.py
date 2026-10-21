"""Exercise the real HA writer; its standard test fixture mocks this method."""

import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from homeassistant.core import CoreState
from homeassistant.helpers.storage import Store
from homeassistant.util.file import WriteError
from homeassistant.util.json import SerializationError

from custom_components.hano.errors import HanoError
from custom_components.hano.storage import StrictStore

# Capture at test collection, before hass_storage replaces the parent method.
_REAL_ASYNC_WRITE_DATA = Store._async_write_data


async def read_saved(store):
    return json.loads(
        await store.hass.async_add_executor_job(Path(store.path).read_text)
    )


async def file_exists(store):
    return await store.hass.async_add_executor_job(Path(store.path).exists)


@pytest.fixture
def real_store(hass, tmp_path):
    """Restore only this write path and keep every resulting file isolated."""
    with (
        patch.object(Store, "_async_write_data", _REAL_ASYNC_WRITE_DATA),
        patch.object(hass.config, "config_dir", str(tmp_path)),
    ):
        yield StrictStore(hass, 1, "hano.storage_test", atomic_writes=True)


async def test_success_means_atomic_file_is_already_written(real_store):
    payload = {"notifications": {"washer": {"status": "active"}}}
    await real_store.async_save(payload)
    saved = await read_saved(real_store)
    assert saved == {
        "version": 1,
        "minor_version": 1,
        "key": "hano.storage_test",
        "data": payload,
    }


@pytest.mark.parametrize(
    "failure", [WriteError("disk full"), OSError("permission denied")]
)
async def test_real_writer_failure_propagates_before_acknowledgement(
    real_store, failure
):
    with patch.object(
        real_store, "_write_prepared_data", side_effect=failure
    ) as writer:
        with pytest.raises(HanoError) as error:
            await real_store.async_save({"notifications": {"washer": "active"}})
    writer.assert_called_once()
    assert error.value.code == "storage_error"
    assert error.value.__cause__ is failure
    assert str(failure) not in error.value.detail
    assert not await file_exists(real_store)
    assert real_store._data is None


async def test_real_serialization_failure_propagates_without_writing(real_store):
    with pytest.raises(HanoError) as error:
        await real_store.async_save({"not_json": object()})
    assert error.value.code == "storage_error"
    assert isinstance(error.value.__cause__, SerializationError)
    assert not await file_exists(real_store)


async def test_failure_does_not_replace_previous_durable_state(real_store):
    await real_store.async_save({"revision": 1})
    with patch.object(
        real_store, "_write_prepared_data", side_effect=WriteError("full")
    ):
        with pytest.raises(HanoError):
            await real_store.async_save({"revision": 2})
    assert (await read_saved(real_store))["data"] == {"revision": 1}
    await real_store.async_save({"revision": 3})
    assert (await read_saved(real_store))["data"] == {"revision": 3}


async def test_shutdown_never_defers_or_acknowledges_a_write(real_store, hass):
    with (
        patch.object(hass, "state", CoreState.stopping),
        patch.object(real_store, "_write_prepared_data", Mock()) as writer,
    ):
        with pytest.raises(HanoError) as error:
            await real_store.async_save({"notification": "must not be sent"})
    assert error.value.code == "storage_error"
    writer.assert_not_called()
    assert real_store._data is None
    assert real_store._unsub_final_write_listener is None


async def test_write_queued_before_shutdown_is_rejected_when_lock_releases(
    real_store, hass
):
    await real_store._write_lock.acquire()
    saving = asyncio.create_task(real_store.async_save({"notification": "pending"}))
    await asyncio.sleep(0)
    with patch.object(hass, "state", CoreState.stopping):
        real_store._write_lock.release()
        with pytest.raises(HanoError) as error:
            await saving
    assert error.value.code == "storage_error"
    assert not await file_exists(real_store)
    assert real_store._unsub_final_write_listener is None


async def test_cancellation_is_not_mislabeled_as_storage_failure(real_store):
    with patch.object(
        real_store, "_write_prepared_data", side_effect=asyncio.CancelledError
    ):
        with pytest.raises(asyncio.CancelledError):
            await real_store.async_save({"notification": "pending"})
