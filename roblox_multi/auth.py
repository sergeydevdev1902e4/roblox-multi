import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional

USER_AGENT = "RobloxMulti/0.2.0 (Windows NT 10.0; Win64; x64)"


class RobloxAuthError(Exception):
    pass


class RobloxAuth:
    """Communicates with Roblox web APIs to verify sessions and generate launch tickets."""

    def __init__(self, cookie: str):
        self.cookie = cookie.strip()
        self.csrf_token: Optional[str] = None

    def _headers(self, send_csrf: bool = True) -> Dict[str, str]:
        headers = {
            "User-Agent": USER_AGENT,
            "Cookie": f".ROBLOSECURITY={self.cookie}",
            "Accept": "application/json",
            "Referer": "https://www.roblox.com/",
            "Origin": "https://www.roblox.com",
        }
        if send_csrf and self.csrf_token:
            headers["x-csrf-token"] = self.csrf_token
        return headers

    def _fetch_csrf_token(self):
        req = urllib.request.Request(
            "https://auth.roblox.com/v1/login",
            headers=self._headers(send_csrf=False),
            data=b"{}",
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except urllib.error.HTTPError as e:
            token = e.headers.get("x-csrf-token")
            if token:
                self.csrf_token = token
                return
            raise RobloxAuthError(f"Could not obtain CSRF token: HTTP {e.code}")
        except Exception as e:
            raise RobloxAuthError(f"Network error obtaining CSRF token: {e}")

    def validate_cookie(self) -> Tuple[int, str, str]:
        req = urllib.request.Request(
            "https://users.roblox.com/v1/users/authenticated",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                user_id = data.get("id")
                username = data.get("name", "")
                display_name = data.get("displayName", username)
                return user_id, username, display_name
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise RobloxAuthError("Cookie is invalid or session has expired.")
            raise RobloxAuthError(f"User validation failed: HTTP {e.code}")
        except Exception as e:
            raise RobloxAuthError(f"Connection error: {e}")

    def get_auth_ticket(self) -> str:
        if not self.csrf_token:
            self._fetch_csrf_token()

        req = urllib.request.Request(
            "https://auth.roblox.com/v1/authentication-ticket",
            headers=self._headers(),
            data=b"{}",
            method="POST",
        )
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                ticket = resp.headers.get("rbx-authentication-ticket")
                if not ticket:
                    raise RobloxAuthError("Roblox did not return an authentication ticket header.")
                return ticket
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # token might have expired, refresh once
                token = e.headers.get("x-csrf-token")
                if token and token != self.csrf_token:
                    self.csrf_token = token
                    return self.get_auth_ticket()
            raise RobloxAuthError(f"Failed to generate game launch ticket: HTTP {e.code}")
        except Exception as e:
            raise RobloxAuthError(f"Network error generating ticket: {e}")
