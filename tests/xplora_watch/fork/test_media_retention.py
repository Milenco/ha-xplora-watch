"""Fork: `media_retention_hours` -- old chat media is not downloaded and is purged from www/."""

from __future__ import annotations

import os
import time
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant

from custom_components.xplora_watch.config import resolve
from custom_components.xplora_watch.const import ATTR_SERVICE_READ_MSG, CONF_MEDIA_RETENTION_HOURS, DOMAIN
from custom_components.xplora_watch.coordinator import XploraDataUpdateCoordinator
from custom_components.xplora_watch.helper import chat_create_epoch, purge_chat_media
from custom_components.xplora_watch.services import XploraMessageSensorUpdateService
from tests.xplora_watch.fixtures.graphql_payloads import DEFAULT_WUID

from ..conftest import setup_service_target
from ..services.test_read_message_service import _make_raw_chat


def test_chat_create_epoch_accepts_seconds_and_millis() -> None:
    assert chat_create_epoch({"create": 1700000000}) == 1700000000
    assert chat_create_epoch({"create": 1700000000000}) == 1700000000
    assert chat_create_epoch({"create": None}) is None
    assert chat_create_epoch({}) is None


def test_purge_removes_old_chat_media_but_keeps_watch_picture(tmp_path) -> None:
    now = time.time()
    old, new = now - 50 * 3600, now - 1 * 3600
    files = {
        "voice/old.mp3": old,
        "voice/new.mp3": new,
        "image/old.jpeg": old,
        "image/WATCH.jpeg": old,  # the watch's own picture
        "video/old.mp4": old,
        "video/thumb/old.jpeg": old,
    }
    for rel, mtime in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
        os.utime(path, (mtime, mtime))
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "old.js").write_bytes(b"x")
    os.utime(tmp_path / "other" / "old.js", (old, old))

    removed = purge_chat_media(str(tmp_path), 48, {"WATCH"}, now=now)

    assert removed == 4
    assert sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file()) == [
        "image/WATCH.jpeg",
        "other/old.js",
        "voice/new.mp3",
    ]


def test_purge_off_keeps_everything(tmp_path) -> None:
    (tmp_path / "voice").mkdir()
    f = tmp_path / "voice" / "x.mp3"
    f.write_bytes(b"x")
    os.utime(f, (1, 1))
    assert purge_chat_media(str(tmp_path), 0, set()) == 0
    assert f.exists()


async def test_read_message_skips_media_of_old_messages(
    hass: HomeAssistant, coordinator_with_data: XploraDataUpdateCoordinator, graphql_operations
) -> None:
    recent = _make_raw_chat("recent", "IMAGE")
    recent["create"] = int(time.time()) - 3600
    old = _make_raw_chat("old", "VOICE")
    old["create"] = int(time.time()) - 72 * 3600
    graphql_operations["Chats"] = {"data": {"chatsNew": {"offset": 0, "limit": 10, "list": [recent, old]}}}
    graphql_operations["setReadChatMsg"] = {"data": {"setReadChatMsg": {}}}
    devices = await setup_service_target(hass, coordinator_with_data)
    hass.config_entries.async_update_entry(
        coordinator_with_data._entry, options={**coordinator_with_data._entry.options, CONF_MEDIA_RETENTION_HOURS: 48}
    )
    assert resolve(coordinator_with_data._entry.options).media_retention_hours == 48

    with (
        patch.object(XploraMessageSensorUpdateService, "_fetch_chat_voice", new=AsyncMock()) as mock_voice,
        patch.object(XploraMessageSensorUpdateService, "_fetch_chat_image", new=AsyncMock()) as mock_image,
        patch("custom_components.xplora_watch.services.purge_chat_media", return_value=0) as mock_purge,
    ):
        await hass.services.async_call(DOMAIN, ATTR_SERVICE_READ_MSG, {"device_id": [devices[DEFAULT_WUID]]}, blocking=True)

    mock_image.assert_awaited_once_with(coordinator_with_data, DEFAULT_WUID, "recent")
    mock_voice.assert_not_awaited()  # 72 h old -> not downloaded
    mock_purge.assert_called_once()
    assert DEFAULT_WUID in mock_purge.call_args.args[2]  # the watch picture is kept
