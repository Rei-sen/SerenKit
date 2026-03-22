import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ..shared.github.updates import (
    DEFAULT_UPDATE_CHECK_INTERVAL,
    build_latest_release_url,
    check_for_updates,
    extract_github_repo,
    fetch_latest_release,
    format_datetime_iso,
    get_current_timestamp,
    is_version_newer,
    load_addon_manifest,
    normalize_version,
    parse_timestamp,
    parse_version,
    should_check_for_updates,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_extract_github_repo_from_manifest_website() -> None:
    repo = extract_github_repo("https://github.com/Rei-sen/SerenKit")
    assert repo == "Rei-sen/SerenKit"


def test_build_latest_release_url() -> None:
    url = build_latest_release_url("Rei-sen/SerenKit")
    assert (
        url == "https://api.github.com/repos/Rei-sen/SerenKit/releases/latest"
    )


def test_normalize_and_parse_version() -> None:
    assert normalize_version("v1.2.3") == "1.2.3"
    assert parse_version("v1.2.3") == (1, 2, 3)


def test_is_version_newer() -> None:
    assert is_version_newer("v0.3.0", "0.2.0") is True
    assert is_version_newer("0.2.0", "0.2.0") is False


def test_get_current_timestamp_round_trips() -> None:
    now = get_current_timestamp()
    parsed = parse_timestamp(format_datetime_iso(now))

    assert parsed is not None


def test_should_check_for_updates_when_no_timestamp() -> None:
    assert should_check_for_updates("") is True


def test_should_check_for_updates_after_interval() -> None:
    now = datetime(2026, 3, 22, 12, 0)
    last_checked = "2026-03-21 23:59:59"

    assert (
        should_check_for_updates(
            last_checked,
            now=now,
            interval=DEFAULT_UPDATE_CHECK_INTERVAL,
        )
        is True
    )


def test_should_not_check_for_updates_before_interval() -> None:
    now = datetime(2026, 3, 22, 12, 0)
    last_checked_at = "2026-03-22 10:00:00"

    assert (
        should_check_for_updates(
            last_checked_at,
            now=now,
            interval=timedelta(hours=12),
        )
        is False
    )


def test_load_addon_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "blender_manifest.toml"
    manifest_path.write_text(
        'version = "1.2.3"\nwebsite = "https://github.com/example/repo"\n',
        encoding="utf-8",
    )

    manifest = load_addon_manifest(manifest_path)

    assert manifest.version == "1.2.3"
    assert manifest.website == "https://github.com/example/repo"


def test_fetch_latest_release_uses_tag_name_and_html_url() -> None:
    def fake_opener(request, timeout: float = 0) -> _FakeResponse:
        assert request.full_url.endswith("/releases/latest")
        return _FakeResponse(
            {
                "tag_name": "v0.3.0",
                "html_url": "https://github.com/Rei-sen/SerenKit/releases/tag/v0.3.0",
            }
        )

    release = fetch_latest_release("Rei-sen/SerenKit", opener=fake_opener)

    assert release.tag_name == "v0.3.0"
    assert release.html_url.endswith("/v0.3.0")


def test_check_for_updates_compares_manifest_and_release(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "blender_manifest.toml"
    manifest_path.write_text(
        'version = "0.2.0"\nwebsite = "https://github.com/Rei-sen/SerenKit"\n',
        encoding="utf-8",
    )

    def fake_opener(request, timeout: float = 0) -> _FakeResponse:
        return _FakeResponse(
            {
                "tag_name": "v0.3.0",
                "html_url": "https://github.com/Rei-sen/SerenKit/releases/tag/v0.3.0",
            }
        )

    result = check_for_updates(manifest_path=manifest_path, opener=fake_opener)

    assert result.current_version == "0.2.0"
    assert result.latest_version == "v0.3.0"
    assert result.is_update_available is True


def test_extract_github_repo_rejects_non_github_urls() -> None:
    with pytest.raises(ValueError):
        extract_github_repo("https://example.com/Rei-sen/SerenKit")


def test_fetch_latest_release_requires_tag_name() -> None:
    def fake_opener(request, timeout: float = 0) -> _FakeResponse:
        return _FakeResponse(
            {"html_url": "https://github.com/Rei-sen/SerenKit"}
        )

    with pytest.raises(ValueError):
        fetch_latest_release("Rei-sen/SerenKit", opener=fake_opener)
