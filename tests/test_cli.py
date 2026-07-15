import pytest
from unittest.mock import patch
from roblox_multi.cli import build_parser, run_cli


def test_parser_add_profile():
    parser = build_parser()
    args = parser.parse_args(["add", "main", "--cookie", "testcookie123"])
    assert args.command == "add"
    assert args.name == "main"
    assert args.cookie == "testcookie123"


def test_parser_list():
    parser = build_parser()
    args = parser.parse_args(["list"])
    assert args.command == "list"


def test_parser_remove():
    parser = build_parser()
    args = parser.parse_args(["remove", "alt_account"])
    assert args.command == "remove"
    assert args.name == "alt_account"


def test_parser_launch_args():
    parser = build_parser()
    args = parser.parse_args([
        "launch",
        "main",
        "--place-id", "189707",
        "--job-id", "job-abc-123",
        "--no-mutex-patch"
    ])
    assert args.command == "launch"
    assert args.name == "main"
    assert args.place_id == "189707"
    assert args.job_id == "job-abc-123"
    assert args.no_mutex_patch is True


def test_run_cli_nonexistent_profile(tmp_path, capsys):
    # Points storage to temp directory so profile doesn't exist
    with patch("roblox_multi.storage.get_default_data_dir", return_value=tmp_path):
        exit_code = run_cli(["launch", "nonexistent_profile"])
        assert exit_code != 0
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()
