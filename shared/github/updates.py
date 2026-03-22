"""GitHub release update helpers for the add-on."""

from __future__ import annotations

import json
import tomllib

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional, Protocol
from urllib.parse import urlparse
from urllib.request import Request, urlopen


_GITHUB_API_BASE = "https://api.github.com/repos"
_USER_AGENT = "SerenKit-UpdateChecker"
DEFAULT_UPDATE_CHECK_INTERVAL = timedelta(hours=12)


class ResponseReader(Protocol):
    """Protocol for URL opener responses used by the update checker."""

    def read(self) -> bytes: ...

    def __enter__(self) -> ResponseReader: ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...


UrlOpener = Callable[..., ResponseReader]


@dataclass(frozen=True)
class AddonManifest:
    """Subset of add-on manifest data needed for update checks."""

    version: str
    website: str


@dataclass(frozen=True)
class GitHubRelease:
    """Normalized GitHub release metadata."""

    tag_name: str
    html_url: str


@dataclass(frozen=True)
class UpdateCheckResult:
    """Result of comparing the current add-on version to GitHub."""

    current_version: str
    latest_version: str
    is_update_available: bool
    release_url: str


def get_manifest_path() -> Path:
    """Return the repository manifest path."""
    return Path(__file__).resolve().parents[2] / "blender_manifest.toml"


def load_addon_manifest(
    manifest_path: Optional[Path] = None,
) -> AddonManifest:
    """Load version and website from the Blender add-on manifest."""
    path = manifest_path or get_manifest_path()
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    version = data.get("version")
    website = data.get("website")

    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"Manifest missing version: {path}")
    if not isinstance(website, str) or not website.strip():
        raise ValueError(f"Manifest missing website: {path}")

    return AddonManifest(version=version.strip(), website=website.strip())


def extract_github_repo(website: str) -> str:
    """Extract owner/repo from a GitHub repository URL."""

    parsed = urlparse(website)
    if parsed.netloc.lower() != "github.com":
        raise ValueError(f"Website is not a GitHub URL: {website}")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"GitHub URL does not include owner/repo: {website}")

    owner, repo = parts[0], parts[1]
    return f"{owner}/{repo}"


def build_latest_release_url(repo: str) -> str:
    """Build the GitHub API URL for the latest release."""
    return f"{_GITHUB_API_BASE}/{repo}/releases/latest"


def normalize_version(version: str) -> str:
    """Normalize version tags like v1.2.3 or 1.2.3-beta for comparison."""
    normalized = version.strip()
    if normalized.lower().startswith("v"):
        normalized = normalized[1:]

    normalized = normalized.split("+", 1)[0]
    normalized = normalized.split("-", 1)[0]
    return normalized


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a dotted version string into an integer tuple."""
    normalized = normalize_version(version)
    if not normalized:
        raise ValueError("Version string is empty")

    parts = normalized.split(".")
    parsed: list[int] = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"Invalid numeric version component: {version}")
        parsed.append(int(part))
    return tuple(parsed)


def is_version_newer(latest_version: str, current_version: str) -> bool:
    """Return True when the latest version is newer than the current version."""
    return parse_version(latest_version) > parse_version(current_version)


def get_current_timestamp() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now()


def format_datetime_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp(timestamp: str) -> Optional[datetime]:
    """Parse a timestamp saved in preferences."""

    if not timestamp:
        return None

    return datetime.fromisoformat(timestamp)


def should_check_for_updates(
    last_checked_at: str,
    *,
    now: Optional[datetime] = None,
    interval: timedelta = DEFAULT_UPDATE_CHECK_INTERVAL,
) -> bool:
    """Return True when enough time has passed to perform another check."""
    parsed = parse_timestamp(last_checked_at)
    if parsed is None:
        return True

    current_time = now or get_current_timestamp()

    return current_time - parsed >= interval


def fetch_latest_release(
    repo: str,
    *,
    timeout: float = 5.0,
    opener: UrlOpener = urlopen,
) -> GitHubRelease:
    """Fetch latest release metadata from GitHub."""
    request = Request(
        build_latest_release_url(repo),
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )

    with opener(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    tag_name = payload.get("tag_name")
    html_url = payload.get("html_url", "")

    if not isinstance(tag_name, str) or not tag_name.strip():
        raise ValueError("GitHub release response missing tag_name")
    if not isinstance(html_url, str):
        raise ValueError("GitHub release response has invalid html_url")

    return GitHubRelease(tag_name=tag_name.strip(), html_url=html_url.strip())


def check_for_updates(
    *,
    manifest_path: Optional[Path] = None,
    timeout: float = 5.0,
    opener: UrlOpener = urlopen,
) -> UpdateCheckResult:
    """Check the latest GitHub release against the local manifest version."""
    manifest = load_addon_manifest(manifest_path=manifest_path)
    repo = extract_github_repo(manifest.website)
    release = fetch_latest_release(repo, timeout=timeout, opener=opener)

    return UpdateCheckResult(
        current_version=manifest.version,
        latest_version=release.tag_name,
        is_update_available=is_version_newer(
            release.tag_name, manifest.version
        ),
        release_url=release.html_url,
    )
