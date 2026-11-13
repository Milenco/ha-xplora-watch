"""Fork: safe-zone feed entries carry the zone's name (`safezone_name`), address (`addr`) and radius (`rad`)."""

from __future__ import annotations

from typing import Any

from custom_components.xplora_watch.notifications import HighWater, plan_events
from custom_components.xplora_watch.pyxplora_api.model import SimpleChat

ALL = {"notify_call", "notify_sos", "notify_power", "notify_low_power", "notify_safezone"}


def _entry(id: str, type: str, create: int, **data: Any) -> SimpleChat:
    return SimpleChat.from_dict({"id": id, "type": type, "create": create, "sender": {"id": "w-uid"}, "data": data})


def test_zone_name_address_and_radius_from_real_keys() -> None:
    # Key set as seen in a real feed (values synthetic).
    feed = [
        _entry(
            "in",
            "ARRIVE_SAFE_ZONE",
            300,
            safezone_name="School",
            safezone_id="z-1",
            addr="Schoolstraat 1",
            rad=120,
            lat=52.0,
            lng=6.0,
            battery=70,
            sub_type="x",
            msg_type="y",
        )
    ]
    event = plan_events(feed, mark=HighWater(create=200, ids=frozenset({"x"})), enabled=ALL).events[0]
    assert event.data["zone"] == "School"
    assert event.data["zone_id"] == "z-1"
    assert event.data["address"] == "Schoolstraat 1"
    assert event.data["radius"] == 120
    assert event.data["state"] == "arrive"


def test_numeric_zone_id_becomes_text() -> None:
    feed = [_entry("out", "LEAVE_SAFE_ZONE", 300, safezone_name="Thuis", safezone_id=42)]
    event = plan_events(feed, mark=HighWater(create=200, ids=frozenset({"x"})), enabled=ALL).events[0]
    assert (event.data["zone"], event.data["zone_id"], event.data["state"]) == ("Thuis", "42", "leave")
