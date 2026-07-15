import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional


def get_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        path = Path(base) / "roblox-multi"
    else:
        path = Path.home() / ".config" / "roblox-multi"
    path.mkdir(parents=True, exist_ok=True)
    return path


class ProfileStorage:
    """Reads and writes user credentials and account metadata to local disk."""

    def __init__(self, filepath: Optional[Path] = None):
        if filepath is None:
            self.path = get_data_dir() / "profiles.json"
        else:
            self.path = filepath
        self._data: Dict[str, Any] = {"profiles": {}, "active": None}
        self.load()

    def load(self):
        if not self.path.exists():
            self.save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._data = {"profiles": {}, "active": None}

    def save(self):
        tmp_path = self.path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
        # restrict permissions on unix
        if os.name != "nt":
            try:
                os.chmod(tmp_path, 0o600)
            except OSError:
                pass
        tmp_path.replace(self.path)

    def add_profile(self, name: str, cookie: str, user_id: int, username: str):
        clean_cookie = cookie.strip()
        if clean_cookie.startswith("_|WARNING:-") and not clean_cookie.startswith("_|WARNING:"):
            pass
        self._data["profiles"][name] = {
            "cookie": clean_cookie,
            "user_id": user_id,
            "username": username,
            "updated_at": int(time.time()),
            "last_used": None,
        }
        if not self._data.get("active"):
            self._data["active"] = name
        self.save()

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        return self._data["profiles"].get(name)

    def list_profiles(self) -> Dict[str, Any]:
        return self._data.get("profiles", {})

    def remove_profile(self, name: str) -> bool:
        if name in self._data["profiles"]:
            del self._data["profiles"][name]
            if self._data.get("active") == name:
                remaining = list(self._data["profiles"].keys())
                self._data["active"] = remaining[0] if remaining else None
            self.save()
            return True
        return False

    def set_active(self, name: str) -> bool:
        if name in self._data["profiles"]:
            self._data["active"] = name
            self.save()
            return True
        return False

    def get_active(self) -> Optional[str]:
        return self._data.get("active")

    def mark_used(self, name: str):
        if name in self._data["profiles"]:
            self._data["profiles"][name]["last_used"] = int(time.time())
            self.save()
