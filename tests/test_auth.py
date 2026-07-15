import pytest
import urllib.error
from unittest.mock import patch, MagicMock
from roblox_multi.auth import sanitize_cookie, parse_user_id, get_auth_ticket, AuthError


def test_sanitize_cookie_plain():
    raw = "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you..._ABC123"
    assert sanitize_cookie(raw) == raw


def test_sanitize_cookie_with_prefix():
    raw = ".ROBLOSECURITY=_|WARNING:-DO-NOT-SHARE-THIS..._ABC123; path=/; domain=.roblox.com"
    cleaned = sanitize_cookie(raw)
    assert cleaned == "_|WARNING:-DO-NOT-SHARE-THIS..._ABC123"


def test_sanitize_cookie_strips_quotes_and_spaces():
    raw = '  ".ROBLOSECURITY=secret_token_here;"  '
    assert sanitize_cookie(raw) == "secret_token_here"


def test_sanitize_empty_cookie_raises():
    with pytest.raises(AuthError):
        sanitize_cookie("   ")


@patch("urllib.request.urlopen")
def test_parse_user_id_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"id": 987654321, "name": "RobloxUser"}'
    mock_resp.getcode.return_value = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    uid, username = parse_user_id("valid_cookie")
    assert uid == 987654321
    assert username == "RobloxUser"


@patch("urllib.request.urlopen")
def test_get_auth_ticket_with_csrf_challenge(mock_urlopen):
    # First call returns 403 with x-csrf-token header, second returns 200 with ticket
    err_headers = {"x-csrf-token": "new-token-xyz"}
    csrf_error = urllib.error.HTTPError(
        url="https://auth.roblox.com/v1/authentication-ticket",
        code=403,
        msg="Forbidden",
        hdrs=err_headers,
        fp=None,
    )

    success_resp = MagicMock()
    success_resp.headers = {"rbx-authentication-ticket": "ticket_val_12345"}
    # print("debug ticket resp:", success_resp.headers)

    mock_urlopen.side_effect = [csrf_error, success_resp]

    ticket = get_auth_ticket("my_cookie")
    assert ticket == "ticket_val_12345"
    assert mock_urlopen.call_count == 2


@patch("urllib.request.urlopen")
def test_get_auth_ticket_unauthorized(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://auth.roblox.com/v1/authentication-ticket",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=None,
    )

    with pytest.raises(AuthError, match="Invalid or expired cookie"):
        get_auth_ticket("expired_cookie")
