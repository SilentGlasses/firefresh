"""Tests for extract_firefox's tar-extraction safety guards (path traversal, symlinks, devices)."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from firefox_installer_app.core import FirefoxInstaller


class FakeDistro:
    def __str__(self) -> str:
        return "FakeOS 1.0"


def _make_installer(tmp_path: Path, temp_dir: Path) -> FirefoxInstaller:
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64")
    installer.temp_dir = str(temp_dir)
    return installer


def _build_tar(tar_path: Path, builder) -> None:
    with tarfile.open(tar_path, "w:bz2") as tar:
        builder(tar)


def test_extracts_well_formed_archive(tmp_path):
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    tar_path = temp_dir / "firefox.tar.bz2"

    payload_dir = tmp_path / "payload"
    payload_dir.mkdir()
    (payload_dir / "firefox").mkdir()
    (payload_dir / "firefox" / "firefox").write_bytes(b"#!/bin/sh\necho hi\n")

    with tarfile.open(tar_path, "w:bz2") as tar:
        tar.add(payload_dir / "firefox", arcname="firefox")

    installer = _make_installer(tmp_path, temp_dir)
    extract_dir = installer.extract_firefox(tar_path)

    assert extract_dir == temp_dir / "firefox"
    assert (extract_dir / "firefox").is_file()


def test_rejects_path_traversal_via_dotdot(tmp_path):
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    tar_path = temp_dir / "evil.tar.bz2"

    evil_file = tmp_path / "evil_payload.txt"
    evil_file.write_bytes(b"pwned")

    def builder(tar: tarfile.TarFile) -> None:
        tar.add(evil_file, arcname="../../etc/evil_cron_job")

    _build_tar(tar_path, builder)

    installer = _make_installer(tmp_path, temp_dir)
    with pytest.raises(RuntimeError, match="Unsafe archive path entry rejected"):
        installer.extract_firefox(tar_path)


def test_rejects_absolute_path_member(tmp_path):
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    tar_path = temp_dir / "evil.tar.bz2"

    evil_file = tmp_path / "evil_payload.txt"
    evil_file.write_bytes(b"pwned")

    def builder(tar: tarfile.TarFile) -> None:
        info = tar.gettarinfo(evil_file, arcname="etc/evil")
        info.name = "/etc/evil_absolute"
        with evil_file.open("rb") as f:
            tar.addfile(info, f)

    _build_tar(tar_path, builder)

    installer = _make_installer(tmp_path, temp_dir)
    with pytest.raises(RuntimeError, match="Unsafe archive path entry rejected"):
        installer.extract_firefox(tar_path)


def test_rejects_symlink_member(tmp_path):
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    tar_path = temp_dir / "evil.tar.bz2"

    def builder(tar: tarfile.TarFile) -> None:
        info = tarfile.TarInfo(name="firefox/malicious_link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tar.addfile(info)

    _build_tar(tar_path, builder)

    installer = _make_installer(tmp_path, temp_dir)
    with pytest.raises(RuntimeError, match="Archive link entry rejected"):
        installer.extract_firefox(tar_path)


def test_rejects_hardlink_member(tmp_path):
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    tar_path = temp_dir / "evil.tar.bz2"

    def builder(tar: tarfile.TarFile) -> None:
        info = tarfile.TarInfo(name="firefox/malicious_hardlink")
        info.type = tarfile.LNKTYPE
        info.linkname = "firefox/other"
        tar.addfile(info)

    _build_tar(tar_path, builder)

    installer = _make_installer(tmp_path, temp_dir)
    with pytest.raises(RuntimeError, match="Archive link entry rejected"):
        installer.extract_firefox(tar_path)


def test_rejects_device_node_member(tmp_path):
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    tar_path = temp_dir / "evil.tar.bz2"

    def builder(tar: tarfile.TarFile) -> None:
        info = tarfile.TarInfo(name="firefox/evil_device")
        info.type = tarfile.CHRTYPE
        info.devmajor = 1
        info.devminor = 3
        tar.addfile(info)

    _build_tar(tar_path, builder)

    installer = _make_installer(tmp_path, temp_dir)
    with pytest.raises(RuntimeError, match="Archive device entry rejected"):
        installer.extract_firefox(tar_path)


def test_raises_when_temp_dir_not_initialized(tmp_path):
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64")
    installer.temp_dir = None

    with pytest.raises(RuntimeError, match="Temporary directory was not initialized"):
        installer.extract_firefox(tmp_path / "whatever.tar.bz2")


def test_raises_when_firefox_dir_missing_after_extraction(tmp_path):
    temp_dir = tmp_path / "work"
    temp_dir.mkdir()
    tar_path = temp_dir / "no_firefox_dir.tar.bz2"

    payload = tmp_path / "not_firefox.txt"
    payload.write_bytes(b"data")

    def builder(tar: tarfile.TarFile) -> None:
        tar.add(payload, arcname="not_firefox/readme.txt")

    _build_tar(tar_path, builder)

    installer = _make_installer(tmp_path, temp_dir)
    with pytest.raises(RuntimeError, match="Firefox directory not found"):
        installer.extract_firefox(tar_path)
