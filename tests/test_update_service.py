import pytest
from pathlib import Path


def test_is_newer_version_compares_semver_strings(test_db):
    from services.update_service import is_newer_version

    assert is_newer_version("1.0.2", "1.0.1") is True
    assert is_newer_version("v1.2.0", "1.1.9") is True
    assert is_newer_version("1.0.1", "1.0.1") is False
    assert is_newer_version("1.0.0", "1.0.1") is False


def test_select_windows_exe_asset_prefers_benchabird_exe(test_db):
    from services.update_service import select_windows_exe_asset

    release = {
        "assets": [
            {"name": "notes.txt", "browser_download_url": "https://example.test/notes.txt"},
            {"name": "benchabird.exe", "browser_download_url": "https://example.test/benchabird.exe"},
            {"name": "other.exe", "browser_download_url": "https://example.test/other.exe"},
        ]
    }

    asset = select_windows_exe_asset(release)

    assert asset["name"] == "benchabird.exe"


def test_install_update_rejects_source_mode(test_db, monkeypatch):
    from services.update_service import UpdateError, install_downloaded_update

    temp_dir = Path.cwd() / ".test_update_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    downloaded = temp_dir / "benchabird.exe"
    downloaded.write_bytes(b"fake exe")
    monkeypatch.setattr("sys.frozen", False, raising=False)

    with pytest.raises(UpdateError, match="packaged app"):
        install_downloaded_update(downloaded, "Changes")
