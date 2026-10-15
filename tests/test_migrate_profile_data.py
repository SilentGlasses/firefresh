"""Tests for migrate_profile_data's symlink-escape guards and migration source handling."""

from __future__ import annotations

import os

import pytest

from firefox_installer_app.core import FirefoxInstaller


class FakeDistro:
    def __str__(self) -> str:
        return "FakeOS 1.0"


def _installer(strict_security: bool = False) -> FirefoxInstaller:
    return FirefoxInstaller(distro=FakeDistro(), arch="x86_64", strict_security=strict_security)


def _patch_target_user(monkeypatch, home_dir):
    monkeypatch.setattr(
        FirefoxInstaller,
        "_resolve_target_user",
        staticmethod(lambda: ("testuser", home_dir, os.getuid(), os.getgid())),
    )
    monkeypatch.setattr(FirefoxInstaller, "_chown_recursive", staticmethod(lambda path, uid, gid: None))


def test_skips_migration_when_target_already_present(tmp_path, monkeypatch):
    home = tmp_path / "home" / "testuser"
    (home / ".mozilla" / "firefox").mkdir(parents=True)
    _patch_target_user(monkeypatch, home)

    installer = _installer()
    installer.migrate_profile_data()

    messages = [e.message for e in installer.reporter.events]
    assert any("already present" in m for m in messages)


def test_migrates_from_snap_source_when_present(tmp_path, monkeypatch):
    home = tmp_path / "home" / "testuser"
    snap_profile = home / "snap" / "firefox" / "common" / ".mozilla" / "firefox"
    snap_profile.mkdir(parents=True)
    (snap_profile / "profiles.ini").write_text("[General]\n")
    _patch_target_user(monkeypatch, home)

    installer = _installer()
    installer.migrate_profile_data()

    target = home / ".mozilla" / "firefox"
    assert target.exists()
    assert (target / "profiles.ini").read_text() == "[General]\n"


def test_skips_source_with_symlinked_entry_when_lenient(tmp_path, monkeypatch):
    home = tmp_path / "home" / "testuser"
    snap_profile = home / "snap" / "firefox" / "common" / ".mozilla" / "firefox"
    snap_profile.mkdir(parents=True)
    outside_target = tmp_path / "outside_secret"
    outside_target.write_text("secret")
    (snap_profile / "evil_link").symlink_to(outside_target)
    _patch_target_user(monkeypatch, home)

    installer = _installer(strict_security=False)
    installer.migrate_profile_data()

    target = home / ".mozilla" / "firefox"
    assert not target.exists()
    messages = [e.message for e in installer.reporter.events]
    assert any("No Snap/Flatpak" in m for m in messages)


def test_raises_on_symlinked_entry_when_strict(tmp_path, monkeypatch):
    home = tmp_path / "home" / "testuser"
    snap_profile = home / "snap" / "firefox" / "common" / ".mozilla" / "firefox"
    snap_profile.mkdir(parents=True)
    outside_target = tmp_path / "outside_secret"
    outside_target.write_text("secret")
    (snap_profile / "evil_link").symlink_to(outside_target)
    _patch_target_user(monkeypatch, home)

    installer = _installer(strict_security=True)
    with pytest.raises(RuntimeError, match="Symlinked entry found"):
        installer.migrate_profile_data()


def test_no_migration_when_no_sources_exist(tmp_path, monkeypatch):
    home = tmp_path / "home" / "testuser"
    home.mkdir(parents=True)
    _patch_target_user(monkeypatch, home)

    installer = _installer()
    installer.migrate_profile_data()

    target = home / ".mozilla" / "firefox"
    assert not target.exists()
    messages = [e.message for e in installer.reporter.events]
    assert any("No Snap/Flatpak" in m for m in messages)


def test_skips_empty_migration_source(tmp_path, monkeypatch):
    home = tmp_path / "home" / "testuser"
    snap_profile = home / "snap" / "firefox" / "common" / ".mozilla" / "firefox"
    snap_profile.mkdir(parents=True)  # empty directory
    _patch_target_user(monkeypatch, home)

    installer = _installer()
    installer.migrate_profile_data()

    target = home / ".mozilla" / "firefox"
    assert not target.exists()
