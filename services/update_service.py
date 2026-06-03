from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

from config import APP_VERSION, DATA_DIR, RELEASE_API_URL

PENDING_CHANGELOG = DATA_DIR / "benchabird_pending_changelog.txt"


class UpdateError(Exception):
    pass


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    changelog: str
    asset_name: str
    asset_url: str


def _version_tuple(value: str) -> tuple[int, ...]:
    cleaned = (value or "").strip().lower().removeprefix("v")
    parts = []
    for part in cleaned.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits or "0"))
    return tuple(parts or [0])


def is_newer_version(latest: str, current: str = APP_VERSION) -> bool:
    latest_parts = _version_tuple(latest)
    current_parts = _version_tuple(current)
    width = max(len(latest_parts), len(current_parts))
    latest_parts += (0,) * (width - len(latest_parts))
    current_parts += (0,) * (width - len(current_parts))
    return latest_parts > current_parts


def select_windows_exe_asset(release: dict) -> dict | None:
    assets = release.get("assets") or []
    exe_assets = [
        asset
        for asset in assets
        if str(asset.get("name") or "").lower().endswith(".exe")
        and asset.get("browser_download_url")
    ]
    if not exe_assets:
        return None
    for asset in exe_assets:
        if "benchabird" in str(asset.get("name") or "").lower():
            return asset
    return exe_assets[0]


def fetch_latest_release(api_url: str = RELEASE_API_URL) -> dict:
    request = urllib.request.Request(api_url, headers={"User-Agent": "Benchabird-Updater"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def check_for_update(current_version: str = APP_VERSION, api_url: str = RELEASE_API_URL) -> UpdateInfo | None:
    release = fetch_latest_release(api_url)
    latest = release.get("tag_name") or release.get("name") or ""
    if not is_newer_version(latest, current_version):
        return None
    asset = select_windows_exe_asset(release)
    if asset is None:
        raise UpdateError("The latest release does not include a Windows .exe asset.")
    return UpdateInfo(
        version=latest,
        changelog=release.get("body") or "No changelog was provided for this release.",
        asset_name=asset.get("name") or "benchabird.exe",
        asset_url=asset.get("browser_download_url"),
    )


def download_update(info: UpdateInfo, destination_dir: Path | None = None) -> Path:
    destination = destination_dir or DATA_DIR
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"downloaded_{info.asset_name}"
    request = urllib.request.Request(info.asset_url, headers={"User-Agent": "Benchabird-Updater"})
    with urllib.request.urlopen(request, timeout=60) as response:
        with target.open("wb") as file:
            shutil.copyfileobj(response, file)
    return target


def _helper_script(downloaded_exe: Path, target_exe: Path, changelog_file: Path) -> str:
    return f"""
$ErrorActionPreference = "Stop"
$downloaded = "{downloaded_exe}"
$target = "{target_exe}"
$changelog = "{changelog_file}"
Start-Sleep -Seconds 2
Copy-Item -LiteralPath $downloaded -Destination $target -Force
Remove-Item -LiteralPath $downloaded -Force
Start-Process -FilePath $target
"""


def install_downloaded_update(downloaded_exe: Path, changelog: str) -> Path:
    if not getattr(sys, "frozen", False):
        raise UpdateError("Updates can only replace the packaged app. Source/dev mode cannot update itself.")

    target_exe = Path(sys.executable)
    helper_path = DATA_DIR / "benchabird_update_helper.ps1"
    PENDING_CHANGELOG.write_text(changelog or "", encoding="utf-8")
    helper_path.write_text(_helper_script(downloaded_exe, target_exe, PENDING_CHANGELOG), encoding="utf-8")
    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(helper_path),
        ],
        cwd=str(DATA_DIR),
        close_fds=True,
    )
    return helper_path


def pop_pending_changelog() -> str | None:
    if not PENDING_CHANGELOG.exists():
        return None
    text = PENDING_CHANGELOG.read_text(encoding="utf-8").strip()
    PENDING_CHANGELOG.unlink(missing_ok=True)
    return text or None
