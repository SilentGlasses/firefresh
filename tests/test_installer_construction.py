"""Tests for FirefoxInstaller construction, channel/arch validation, and download URL building."""

from __future__ import annotations

import pytest

from firefox_installer_app.core import FirefoxInstaller


class FakeDistro:
    def __str__(self) -> str:
        return "FakeOS 1.0"


def test_resolve_architecture_normalizes_known_values():
    machine, os_param = FirefoxInstaller.resolve_architecture("x86_64")
    assert (machine, os_param) == ("x86_64", "linux64")

    machine, os_param = FirefoxInstaller.resolve_architecture("ARM64")
    assert (machine, os_param) == ("arm64", "linux-aarch64")


def test_resolve_architecture_rejects_unknown():
    with pytest.raises(RuntimeError, match="Unsupported architecture"):
        FirefoxInstaller.resolve_architecture("sparc64")


def test_rejects_unsupported_channel():
    with pytest.raises(ValueError, match="Unsupported Firefox channel"):
        FirefoxInstaller(distro=FakeDistro(), channel="stable", arch="x86_64")


def test_builds_expected_download_url_for_channel():
    installer = FirefoxInstaller(distro=FakeDistro(), channel="beta", lang="fr", arch="x86_64")

    assert installer.download_url == (
        "https://download.mozilla.org/?product=firefox-beta-latest-ssl&os=linux64&lang=fr"
    )


def test_default_channel_is_general():
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64")

    assert "product=firefox-latest-ssl" in installer.download_url
