"""Tests for DistroDetector's /etc/os-release parsing and distro resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from firefox_installer_app.core import DistroDetector


def _write_os_release(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_detects_directly_supported_distro(tmp_path, monkeypatch):
    os_release = tmp_path / "os-release"
    _write_os_release(
        os_release,
        'NAME="Ubuntu"\nID=ubuntu\nID_LIKE=debian\nVERSION_ID="24.04"\n',
    )
    monkeypatch.setattr("firefox_installer_app.core.Path", lambda p: os_release if p == "/etc/os-release" else Path(p))

    detector = DistroDetector()

    assert detector.distro_id == "ubuntu"
    assert detector.distro_name == "Ubuntu"
    assert detector.distro_version == "24.04"
    assert detector.get_package_manager() == "/usr/bin/apt"


def test_falls_back_to_id_like_when_id_unsupported(tmp_path, monkeypatch):
    os_release = tmp_path / "os-release"
    _write_os_release(
        os_release,
        'NAME="Linux Mint"\nID=linuxmint\nID_LIKE="ubuntu debian"\nVERSION_ID="21"\n',
    )
    monkeypatch.setattr("firefox_installer_app.core.Path", lambda p: os_release if p == "/etc/os-release" else Path(p))

    detector = DistroDetector()

    assert detector.distro_id == "ubuntu"
    assert detector.get_remove_command() == [
        "/usr/bin/apt",
        "remove",
        "-y",
        "firefox",
        "firefox-geckodriver",
    ]


def test_raises_when_os_release_missing(tmp_path, monkeypatch):
    missing = tmp_path / "does-not-exist"
    monkeypatch.setattr("firefox_installer_app.core.Path", lambda p: missing if p == "/etc/os-release" else Path(p))

    with pytest.raises(RuntimeError, match="os-release not found"):
        DistroDetector()


def test_raises_for_fully_unsupported_distro(tmp_path, monkeypatch):
    os_release = tmp_path / "os-release"
    _write_os_release(
        os_release,
        'NAME="MysteryOS"\nID=mysteryos\nID_LIKE="alienware"\nVERSION_ID="1"\n',
    )
    monkeypatch.setattr("firefox_installer_app.core.Path", lambda p: os_release if p == "/etc/os-release" else Path(p))

    with pytest.raises(RuntimeError, match="Unsupported distribution"):
        DistroDetector()


def test_str_representation(tmp_path, monkeypatch):
    os_release = tmp_path / "os-release"
    _write_os_release(os_release, 'NAME="Fedora"\nID=fedora\nVERSION_ID="41"\n')
    monkeypatch.setattr("firefox_installer_app.core.Path", lambda p: os_release if p == "/etc/os-release" else Path(p))

    detector = DistroDetector()

    assert str(detector) == "Fedora 41"
