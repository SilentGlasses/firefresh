"""Tests for SHA256 checksum verification and the InstallReporter event log."""

from __future__ import annotations

import hashlib
import json

import pytest

from firefox_installer_app.core import FirefoxInstaller, InstallReporter


class FakeDistro:
    def __str__(self) -> str:
        return "FakeOS 1.0"


def test_compute_sha256_matches_hashlib(tmp_path):
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(b"some binary content" * 1000)

    expected = hashlib.sha256(file_path.read_bytes()).hexdigest()
    assert FirefoxInstaller._compute_sha256(file_path) == expected


def test_verify_download_integrity_raises_without_resolved_url(tmp_path):
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64")
    installer.resolved_download_url = ""

    with pytest.raises(RuntimeError, match="Resolved download URL is unavailable"):
        installer.verify_download_integrity(tmp_path / "firefox.tar.bz2")


def test_verify_download_integrity_rejects_mismatched_checksum(tmp_path, monkeypatch):
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64")
    installer.resolved_download_url = (
        "https://download-installer.cdn.mozilla.net/pub/firefox/releases/1.0/"
        "linux-x86_64/en-US/firefox-1.0.tar.bz2"
    )

    tar_path = tmp_path / "firefox-1.0.tar.bz2"
    tar_path.write_bytes(b"actual content")

    wrong_sha = hashlib.sha256(b"different content").hexdigest()

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return f"{wrong_sha} *firefox-1.0.tar.bz2\n".encode()

    monkeypatch.setattr(
        "firefox_installer_app.core.urllib.request.urlopen", lambda *a, **k: FakeResponse()
    )

    with pytest.raises(RuntimeError, match="Checksum mismatch"):
        installer.verify_download_integrity(tar_path)


def test_verify_download_integrity_accepts_matching_checksum(tmp_path, monkeypatch):
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64")
    installer.resolved_download_url = (
        "https://download-installer.cdn.mozilla.net/pub/firefox/releases/1.0/"
        "linux-x86_64/en-US/firefox-1.0.tar.bz2"
    )

    tar_path = tmp_path / "firefox-1.0.tar.bz2"
    tar_path.write_bytes(b"actual content")
    correct_sha = hashlib.sha256(tar_path.read_bytes()).hexdigest()

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return f"{correct_sha} *firefox-1.0.tar.bz2\n".encode()

    monkeypatch.setattr(
        "firefox_installer_app.core.urllib.request.urlopen", lambda *a, **k: FakeResponse()
    )

    installer.verify_download_integrity(tar_path)  # should not raise


def test_verify_download_integrity_uses_allowlisted_checksum_url(tmp_path, monkeypatch):
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64")
    installer.resolved_download_url = "https://evil.example.com/firefox-1.0.tar.bz2"

    tar_path = tmp_path / "firefox-1.0.tar.bz2"
    tar_path.write_bytes(b"data")

    with pytest.raises(RuntimeError, match="untrusted host"):
        installer.verify_download_integrity(tar_path)


def test_verify_download_integrity_strict_mode_raises_on_fetch_failure(tmp_path, monkeypatch):
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64", strict_security=True)
    installer.resolved_download_url = (
        "https://download-installer.cdn.mozilla.net/pub/firefox/releases/1.0/"
        "linux-x86_64/en-US/firefox-1.0.tar.bz2"
    )
    tar_path = tmp_path / "firefox-1.0.tar.bz2"
    tar_path.write_bytes(b"data")

    def boom(*a, **k):
        raise OSError("network unreachable")

    monkeypatch.setattr("firefox_installer_app.core.urllib.request.urlopen", boom)

    with pytest.raises(RuntimeError, match="Checksum retrieval failed"):
        installer.verify_download_integrity(tar_path)


def test_verify_download_integrity_lenient_mode_warns_on_fetch_failure(tmp_path, monkeypatch):
    installer = FirefoxInstaller(distro=FakeDistro(), arch="x86_64", strict_security=False)
    installer.resolved_download_url = (
        "https://download-installer.cdn.mozilla.net/pub/firefox/releases/1.0/"
        "linux-x86_64/en-US/firefox-1.0.tar.bz2"
    )
    tar_path = tmp_path / "firefox-1.0.tar.bz2"
    tar_path.write_bytes(b"data")

    def boom(*a, **k):
        raise OSError("network unreachable")

    monkeypatch.setattr("firefox_installer_app.core.urllib.request.urlopen", boom)

    installer.verify_download_integrity(tar_path)  # should not raise
    assert any("Checksum retrieval failed" in e.message for e in installer.reporter.events)


def test_reporter_summary_counts_by_severity():
    reporter = InstallReporter()
    reporter.add("INFO", "starting")
    reporter.add("WARNING", "careful")
    reporter.add("ERROR", "oops")
    reporter.add("ERROR", "oops again")
    reporter.add("CRITICAL", "boom")

    summary = reporter.summary()

    assert summary == {"INFO": 1, "WARNING": 1, "ERROR": 2, "CRITICAL": 1}


def test_reporter_write_report_file_writes_valid_json(tmp_path):
    report_path = tmp_path / "nested" / "report.json"
    reporter = InstallReporter(report_file=str(report_path))
    reporter.add("INFO", "hello")

    reporter.write_report_file()

    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["summary"]["INFO"] == 1
    assert data["events"][0]["message"] == "hello"


def test_reporter_write_report_file_noop_without_path():
    reporter = InstallReporter(report_file=None)
    reporter.add("INFO", "hello")
    reporter.write_report_file()  # should not raise, no file created
