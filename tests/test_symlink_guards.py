"""Tests for symlink/directory-replacement guards used before destructive filesystem operations."""

from __future__ import annotations

from pathlib import Path

import pytest

from firefox_installer_app.core import FirefoxInstaller


class FakeDistro:
    def __str__(self) -> str:
        return "FakeOS 1.0"


def _installer() -> FirefoxInstaller:
    return FirefoxInstaller(distro=FakeDistro(), arch="x86_64")


def test_ensure_directory_target_allows_missing_path(tmp_path):
    target = tmp_path / "does_not_exist"
    FirefoxInstaller._ensure_directory_target(target, "install prefix")  # no raise


def test_ensure_directory_target_allows_real_directory(tmp_path):
    target = tmp_path / "real_dir"
    target.mkdir()
    FirefoxInstaller._ensure_directory_target(target, "install prefix")  # no raise


def test_ensure_directory_target_rejects_symlink(tmp_path):
    real = tmp_path / "real_dir"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)

    with pytest.raises(RuntimeError, match="Refusing to replace symlinked"):
        FirefoxInstaller._ensure_directory_target(link, "install prefix")


def test_ensure_directory_target_rejects_non_directory(tmp_path):
    target = tmp_path / "a_file"
    target.write_text("not a directory")

    with pytest.raises(RuntimeError, match="Refusing to replace non-directory"):
        FirefoxInstaller._ensure_directory_target(target, "install prefix")


def test_managed_symlink_exists_true_for_matching_target(tmp_path, monkeypatch):
    monkeypatch.setattr(FirefoxInstaller, "FIREFOX_BIN", tmp_path / "opt" / "firefox" / "firefox")
    link = tmp_path / "firefox-link"
    link.symlink_to(FirefoxInstaller.FIREFOX_BIN)

    assert FirefoxInstaller._managed_symlink_exists(link) is True


def test_managed_symlink_exists_false_for_foreign_target(tmp_path):
    link = tmp_path / "firefox-link"
    link.symlink_to("/usr/bin/some-other-browser")

    assert FirefoxInstaller._managed_symlink_exists(link) is False


def test_managed_symlink_exists_false_for_non_symlink(tmp_path):
    real_file = tmp_path / "not_a_link"
    real_file.write_text("plain file")

    assert FirefoxInstaller._managed_symlink_exists(real_file) is False


def test_create_symlink_refuses_unmanaged_existing_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(FirefoxInstaller, "SYMLINK_PATH", tmp_path / "usr_local_bin_firefox")
    monkeypatch.setattr(FirefoxInstaller, "FIREFOX_BIN", tmp_path / "opt_firefox_firefox")
    FirefoxInstaller.SYMLINK_PATH.symlink_to("/usr/bin/chromium")

    installer = _installer()
    with pytest.raises(RuntimeError, match="Refusing to replace unmanaged symlink"):
        installer.create_symlink()


def test_create_symlink_refuses_existing_non_symlink_file(tmp_path, monkeypatch):
    monkeypatch.setattr(FirefoxInstaller, "SYMLINK_PATH", tmp_path / "usr_local_bin_firefox")
    monkeypatch.setattr(FirefoxInstaller, "FIREFOX_BIN", tmp_path / "opt_firefox_firefox")
    FirefoxInstaller.SYMLINK_PATH.write_text("not a symlink")

    installer = _installer()
    with pytest.raises(RuntimeError, match="Refusing to replace existing non-symlink"):
        installer.create_symlink()


def test_create_symlink_replaces_previously_managed_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(FirefoxInstaller, "SYMLINK_PATH", tmp_path / "usr_local_bin_firefox")
    monkeypatch.setattr(FirefoxInstaller, "FIREFOX_BIN", tmp_path / "opt_firefox_firefox")
    FirefoxInstaller.SYMLINK_PATH.symlink_to(FirefoxInstaller.FIREFOX_BIN)

    installer = _installer()
    installer.create_symlink()

    assert FirefoxInstaller.SYMLINK_PATH.is_symlink()
    assert Path(__import__("os").readlink(FirefoxInstaller.SYMLINK_PATH)) == FirefoxInstaller.FIREFOX_BIN


def test_safe_resolve_under_allows_nested_path(tmp_path):
    base = tmp_path / "home" / "user"
    base.mkdir(parents=True)
    nested = base / ".mozilla" / "firefox"

    resolved = FirefoxInstaller._safe_resolve_under(nested, base)

    assert resolved == nested.resolve(strict=False)


def test_safe_resolve_under_allows_base_itself(tmp_path):
    base = tmp_path / "home" / "user"
    base.mkdir(parents=True)

    resolved = FirefoxInstaller._safe_resolve_under(base, base)

    assert resolved == base.resolve(strict=False)


def test_safe_resolve_under_rejects_escape_via_dotdot(tmp_path):
    base = tmp_path / "home" / "user"
    base.mkdir(parents=True)
    escaping = base / ".." / ".." / "etc" / "passwd"

    with pytest.raises(RuntimeError, match="resolves outside expected directory"):
        FirefoxInstaller._safe_resolve_under(escaping, base)


def test_safe_resolve_under_rejects_symlink_escape(tmp_path):
    base = tmp_path / "home" / "user"
    base.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()

    escape_link = base / "snap"
    escape_link.symlink_to(outside)
    candidate = escape_link / "firefox"

    with pytest.raises(RuntimeError, match="resolves outside expected directory"):
        FirefoxInstaller._safe_resolve_under(candidate, base)
