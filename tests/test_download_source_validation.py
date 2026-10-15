"""Tests for the SSRF/host-allowlist guard on download URLs (_validate_download_source)."""

from __future__ import annotations

import pytest

from firefox_installer_app.core import FirefoxInstaller


@pytest.mark.parametrize(
    "url",
    [
        "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US",
        "https://download-installer.cdn.mozilla.net/pub/firefox/releases/1.0/linux-x86_64/en-US/firefox-1.0.tar.bz2",
        "https://archive.mozilla.org/pub/firefox/releases/1.0/SHA256SUMS",
    ],
)
def test_allows_known_mozilla_hosts(url):
    FirefoxInstaller._validate_download_source(url)  # should not raise


def test_rejects_non_https_scheme():
    with pytest.raises(RuntimeError, match="Refusing non-HTTPS"):
        FirefoxInstaller._validate_download_source("http://download.mozilla.org/firefox.tar.bz2")


def test_rejects_untrusted_host():
    with pytest.raises(RuntimeError, match="untrusted host"):
        FirefoxInstaller._validate_download_source("https://evil.example.com/firefox.tar.bz2")


def test_rejects_lookalike_host_via_subdomain_confusion():
    # e.g. "download.mozilla.org.evil.com" must not be treated as mozilla.org
    with pytest.raises(RuntimeError, match="untrusted host"):
        FirefoxInstaller._validate_download_source(
            "https://download.mozilla.org.evil.com/firefox.tar.bz2"
        )


def test_rejects_userinfo_host_confusion():
    # e.g. "https://download.mozilla.org@evil.com/" must resolve hostname as evil.com
    with pytest.raises(RuntimeError, match="untrusted host"):
        FirefoxInstaller._validate_download_source(
            "https://download.mozilla.org@evil.com/firefox.tar.bz2"
        )


def test_rejects_file_scheme():
    with pytest.raises(RuntimeError, match="Refusing non-HTTPS"):
        FirefoxInstaller._validate_download_source("file:///etc/passwd")


def test_hostname_match_is_case_insensitive():
    FirefoxInstaller._validate_download_source(
        "https://DOWNLOAD.MOZILLA.ORG/?product=firefox-latest-ssl"
    )  # should not raise
