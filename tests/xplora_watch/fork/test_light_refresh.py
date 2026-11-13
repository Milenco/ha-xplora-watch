"""Fork: `refresh_location` reads the last stored fix without waking the watch."""

from __future__ import annotations

import re
from typing import Any
from unittest.mock import AsyncMock, patch

from aioresponses import aioresponses
from homeassistant.core import HomeAssistant

from custom_components.xplora_watch.const import ATTR_LAST_UPDATE_STATUS, ATTR_SERVICE_REFRESH_LOCATION, DOMAIN, LAST_UPDATE_NO_RESPONSE
from custom_components.xplora_watch.coordinator import XploraDataUpdateCoordinator
from tests.xplora_watch.fixtures.graphql_payloads import DEFAULT_WUID, make_watch_last_locate_payload

from ..conftest import setup_service_target


def _operations(mocked: aioresponses) -> list[str]:
    """Operation names of the Xplora GraphQL POSTs so far, in order (geocoding GETs excluded)."""
    names: list[str] = []
    for (method, _url), calls in mocked.requests.items():
        if method != "POST":
            continue
        for call in calls:
            body = (call.kwargs or {}).get("json") or {}
            match = re.search(r"(?:query|mutation)\s+(\w+)", body.get("query", ""))
            names.append(body.get("operationName") or (match.group(1) if match else "?"))
    return names


async def test_light_refresh_reads_last_fix_only(
    coordinator_with_data: XploraDataUpdateCoordinator, mock_graphql: aioresponses, graphql_operations: dict[str, Any]
) -> None:
    coord = coordinator_with_data
    graphql_operations["WatchLastLocate"] = {
        "data": make_watch_last_locate_payload(battery=33, lat="52.2084", lng="7.0006", is_charging=True)
    }
    graphql_operations["WatchLastLocate"]["data"]["watchLastLocate"]["tm"] = 1700009999
    before = _operations(mock_graphql)

    data = await coord.async_update_xplora_data([DEFAULT_WUID], light=True)

    new_ops = _operations(mock_graphql)[len(before) :]
    assert new_ops == ["WatchLastLocate"]  # no askWatchLocate (no wake), no deviceList, no feed
    entry = data[DEFAULT_WUID]
    assert entry["battery"] == 33
    assert entry["isCharging"] is True
    assert entry["lat"] == 52.2084
    assert entry["lng"] == 7.0006


async def test_light_refresh_keeps_last_locate_verdict(coordinator_with_data: XploraDataUpdateCoordinator) -> None:
    coord = coordinator_with_data
    coord.data[DEFAULT_WUID][ATTR_LAST_UPDATE_STATUS] = LAST_UPDATE_NO_RESPONSE
    data = await coord.async_update_xplora_data([DEFAULT_WUID], light=True)
    assert data[DEFAULT_WUID][ATTR_LAST_UPDATE_STATUS] == LAST_UPDATE_NO_RESPONSE


async def test_light_refresh_is_not_coalesced_with_a_full_refresh(coordinator_with_data: XploraDataUpdateCoordinator) -> None:
    coord = coordinator_with_data
    await coord.async_update_xplora_data([DEFAULT_WUID], light=True)
    assert coord._inflight_updates == {}


async def test_refresh_location_service_calls_light_refresh(hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
    devices = await setup_service_target(hass, coordinator)
    with patch.object(coordinator, "async_update_xplora_data", new=AsyncMock()) as mock_update:
        await hass.services.async_call(DOMAIN, ATTR_SERVICE_REFRESH_LOCATION, {"device_id": [devices[DEFAULT_WUID]]}, blocking=True)
    mock_update.assert_awaited_once_with([DEFAULT_WUID], light=True)
