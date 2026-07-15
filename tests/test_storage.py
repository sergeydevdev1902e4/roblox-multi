import json
import pytest
from roblox_multi.storage import ProfileStore, StorageError


def test_save_and_get_profile(tmp_path):
    store = ProfileStore(data_dir=tmp_path)
    store.save_profile("main_acc", ".ROBLOSECURITY=_|WARNING:-DO-NOT-SHARE..._test123", user_id=12345)

    profile = store.get_profile("main_acc")
    assert profile["name"] == "main_acc"
    assert profile["user_id"] == 12345
    assert "test123" in profile["cookie"]


def test_list_profiles_empty(tmp_path):
    store = ProfileStore(data_dir=tmp_path)
    assert store.list_profiles() == []


def test_list_multiple_profiles(tmp_path):
    store = ProfileStore(data_dir=tmp_path)
    store.save_profile("alt1", "cookie_a", user_id=101)
    store.save_profile("alt2", "cookie_b", user_id=102)

    profiles = store.list_profiles()
    assert len(profiles) == 2
    names = [p["name"] for p in profiles]
    assert "alt1" in names
    assert "alt2" in names


def test_delete_profile(tmp_path):
    store = ProfileStore(data_dir=tmp_path)
    store.save_profile("temp", "some_cookie", user_id=999)
    assert store.delete_profile("temp") is True
    assert store.get_profile("temp") is None


def test_delete_nonexistent_returns_false(tmp_path):
    store = ProfileStore(data_dir=tmp_path)
    assert store.delete_profile("ghost") is False


def test_corrupt_json_handling(tmp_path):
    db_file = tmp_path / "profiles.json"
    db_file.write_text("{broken json content!", encoding="utf-8")

    store = ProfileStore(data_dir=tmp_path)
    with pytest.raises(StorageError):
        store.list_profiles()


def test_save_overwrites_existing(tmp_path):
    store = ProfileStore(data_dir=tmp_path)
    store.save_profile("bot", "old_cookie", user_id=1)
    store.save_profile("bot", "new_cookie", user_id=1)

    profile = store.get_profile("bot")
    assert profile["cookie"] == "new_cookie"
    assert len(store.list_profiles()) == 1
