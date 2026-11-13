"""Fork: `max_accuracy` keeps inaccurate (cell-tower) fixes from moving the tracker."""

from __future__ import annotations

from typing import Any

from custom_components.xplora_watch.config import resolve
from custom_components.xplora_watch.const import ATTR_IGNORED_FIX, CONF_MAX_ACCURACY
from custom_components.xplora_watch.coordinator import XploraDataUpdateCoordinator
from tests.xplora_watch.fixtures.graphql_payloads import DEFAULT_WUID, make_watch_last_locate_payload


def _set_fix(graphql_operations: dict[str, Any], lat: str, lng: str, rad: int, tm: int, locate_type: str) -> None:
    payload = make_watch_last_locate_payload(lat=lat, lng=lng)
    payload["watchLastLocate"].update({"rad": rad, "tm": tm, "locateType": locate_type})
    graphql_operations["WatchLastLocate"] = {"data": payload}


def _set_option(hass, coord: XploraDataUpdateCoordinator, value: int) -> None:
    # Options are resolved once per setup; in Home Assistant an options change reloads the entry.
    coord._resolved = resolve({**coord._entry.options, CONF_MAX_ACCURACY: value})


async def test_inaccurate_fix_keeps_previous_position(hass, coordinator_with_data: XploraDataUpdateCoordinator, graphql_operations) -> None:
    coord = coordinator_with_data
    _set_option(hass, coord, 300)
    _set_fix(graphql_operations, "52.2084", "7.0006", 20, 1700001000, "GPS")
    good = (await coord.async_update_xplora_data([DEFAULT_WUID], light=True))[DEFAULT_WUID]
    assert (good["lat"], good["lng"]) == (52.2084, 7.0006)
    assert good[ATTR_IGNORED_FIX] is None

    _set_fix(graphql_operations, "52.2500", "6.9000", 1500, 1700002000, "LBS")
    data = (await coord.async_update_xplora_data([DEFAULT_WUID], light=True))[DEFAULT_WUID]
    assert (data["lat"], data["lng"]) == (52.2084, 7.0006)  # previous position kept
    assert data["location_accuracy"] == 20
    assert data[ATTR_IGNORED_FIX]["accuracy"] == 1500
    assert data[ATTR_IGNORED_FIX]["locate_type"] == "LBS"


async def test_filter_off_moves_tracker(hass, coordinator_with_data: XploraDataUpdateCoordinator, graphql_operations) -> None:
    coord = coordinator_with_data
    _set_option(hass, coord, 0)
    _set_fix(graphql_operations, "52.2500", "6.9000", 1500, 1700002000, "LBS")
    data = (await coord.async_update_xplora_data([DEFAULT_WUID], light=True))[DEFAULT_WUID]
    assert (data["lat"], data["lng"]) == (52.25, 6.9)
    assert data[ATTR_IGNORED_FIX] is None
