"""Fork: logging in as Xplora's web client (`WEB`) next to the phone app (`APP`)."""

from __future__ import annotations

from custom_components.xplora_watch.config_flow import client_type_for
from custom_components.xplora_watch.const import CONF_WEB_CLIENT
from custom_components.xplora_watch.pyxplora_api.const import API_KEY, API_SECRET, WEB_API_KEY, WEB_API_SECRET, WEB_ORIGIN
from custom_components.xplora_watch.pyxplora_api.gql_handler_async import GQLHandler
from custom_components.xplora_watch.pyxplora_api.pyxplora_api_async import PyXploraApi


def test_app_client_is_unchanged() -> None:
    handler = GQLHandler("+49", "0151 234", "pw", "en-GB", "Europe/Berlin", email=None, signup=False)
    assert handler.variables["client"] == "APP"
    assert handler.variables["countryPhoneNumber"] == "+49"  # upstream sends it as entered
    headers = handler.getRequestHeaders("application/json")
    assert headers["H-BackDoor-Authorization"] == f"Open {API_KEY}:{API_SECRET}"
    assert "Origin" not in headers


def test_web_client_login_variables_and_open_headers() -> None:
    handler = GQLHandler("+31", "6 1234-5678", "pw", "nl-NL", "Europe/Amsterdam", signup=False, clientType="WEB")
    assert handler.variables["client"] == "WEB"
    # Digits only, as the tested web login sends them.
    assert handler.variables["countryPhoneNumber"] == "31"
    assert handler.variables["phoneNumber"] == "612345678"
    headers = handler.getRequestHeaders("application/json")
    assert headers["H-BackDoor-Authorization"] == f"Open {WEB_API_KEY}:{WEB_API_SECRET}"
    assert headers["Origin"] == WEB_ORIGIN
    assert WEB_API_KEY != API_KEY


def test_web_client_signs_requests_with_the_static_web_secret() -> None:
    handler = GQLHandler("31", "612345678", "pw", "nl-NL", "Europe/Amsterdam", signup=False, clientType="WEB")
    handler.accessToken = "tok"
    handler.issueToken = {"token": "tok"}
    headers = handler.getRequestHeaders("application/json")
    assert headers["H-BackDoor-Authorization"] == f"Bearer tok:{WEB_API_SECRET}"


def test_client_type_survives_a_reset() -> None:
    api = PyXploraApi("31", "612345678", "pw", "nl-NL", "Europe/Amsterdam", client_type="WEB")
    assert api._gql_handler.variables["client"] == "WEB"
    api._reset(countrycode="31", phoneNumber="612345678", password="pw", userLang="nl-NL", timeZone="Europe/Amsterdam")
    assert api._gql_handler.variables["client"] == "WEB"


def test_client_type_for_entry_data() -> None:
    assert client_type_for({CONF_WEB_CLIENT: True}) == "WEB"
    assert client_type_for({CONF_WEB_CLIENT: False}) == "APP"
    assert client_type_for({}) == "APP"  # entries created before the fork option
