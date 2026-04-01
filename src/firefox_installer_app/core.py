"""Core logic for distro-aware Firefox installation."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import pwd
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class InstallEvent:
    """A structured installer report event."""

    timestamp: str
    severity: str
    message: str


class InstallReporter:
    """Collect and emit installer events for user-facing reporting."""

    def __init__(self, report_file: str | None = None) -> None:
        self.events: list[InstallEvent] = []
        self.report_file = report_file

    def add(self, severity: str, message: str) -> None:
        event = InstallEvent(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            severity=severity,
            message=message,
        )
        self.events.append(event)

    def summary(self) -> dict[str, int]:
        counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        for event in self.events:
            if event.severity in counts:
                counts[event.severity] += 1
        return counts

    def print_report(self) -> None:
        print("\n" + "=" * 72)
        print("Firefox Installer Report")
        print("=" * 72)
        for event in self.events:
            print(f"[{event.severity}] {event.timestamp} - {event.message}")

        counts = self.summary()
        print("-" * 72)
        print(
            "Summary: "
            f"INFO={counts['INFO']} "
            f"WARNING={counts['WARNING']} "
            f"ERROR={counts['ERROR']} "
            f"CRITICAL={counts['CRITICAL']}"
        )
        print("=" * 72)

    def write_report_file(self) -> None:
        if not self.report_file:
            return

        path = Path(self.report_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "summary": self.summary(),
                    "events": [asdict(event) for event in self.events],
                },
                indent=2,
            ),
            encoding="utf-8",
        )


class DistroDetector:
    """Detect Linux distribution and provide distro-specific commands."""

    DISTROS = {
        "ubuntu": {"pm": "apt", "remove": ["apt", "remove", "-y", "firefox", "firefox-geckodriver"]},
        "debian": {"pm": "apt", "remove": ["apt", "remove", "-y", "firefox", "firefox-geckodriver"]},
        "fedora": {"pm": "dnf", "remove": ["dnf", "remove", "-y", "firefox"]},
        "centos": {"pm": "yum", "remove": ["yum", "remove", "-y", "firefox"]},
        "rhel": {"pm": "yum", "remove": ["yum", "remove", "-y", "firefox"]},
        "arch": {"pm": "pacman", "remove": ["pacman", "-R", "--noconfirm", "firefox"]},
        "manjaro": {"pm": "pacman", "remove": ["pacman", "-R", "--noconfirm", "firefox"]},
        "opensuse": {"pm": "zypper", "remove": ["zypper", "remove", "-y", "firefox"]},
        "alpine": {"pm": "apk", "remove": ["apk", "del", "firefox"]},
    }

    def __init__(self) -> None:
        self.distro_name = "Unknown"
        self.distro_version = "Unknown"
        self.distro_id = ""
        self._detect()

    def _detect(self) -> None:
        os_release_file = Path("/etc/os-release")
        if not os_release_file.exists():
            raise RuntimeError("Cannot detect OS: /etc/os-release not found")

        data = {}
        with os_release_file.open("r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.split("=", 1)
                    data[key.strip()] = value.strip().strip('"')

        self.distro_id = data.get("ID", "").lower()
        self.distro_name = data.get("NAME", "Unknown")
        self.distro_version = data.get("VERSION_ID", "Unknown")

        if self.distro_id not in self.DISTROS:
            for parent_id in data.get("ID_LIKE", "").lower().split():
                if parent_id in self.DISTROS:
                    self.distro_id = parent_id
                    break

        if self.distro_id not in self.DISTROS:
            raise RuntimeError(
                f"Unsupported distribution: {self.distro_name}. Detected ID: {self.distro_id}"
            )

    def get_remove_command(self) -> list[str]:
        return self.DISTROS[self.distro_id]["remove"]

    def get_package_manager(self) -> str:
        return self.DISTROS[self.distro_id]["pm"]

    def __str__(self) -> str:
        return f"{self.distro_name} {self.distro_version}".strip()


class FirefoxInstaller:
    """Install and uninstall Firefox from Mozilla binaries."""

    DOWNLOAD_TIMEOUT_SECONDS = 120
    ALLOWED_DOWNLOAD_HOSTS = {
        "download.mozilla.org",
        "download-installer.cdn.mozilla.net",
        "archive.mozilla.org",
    }

    SAFE_EXEC_ENV = {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": "/root",
    }

    CHANNEL_PRODUCT_MAP = {
        "general": "firefox-latest-ssl",
        "beta": "firefox-beta-latest-ssl",
        "nightly": "firefox-nightly-latest-ssl",
        "developer": "firefox-devedition-latest-ssl",
        "esr": "firefox-esr-latest-ssl",
    }

    ARCH_OS_MAP = {
        "x86_64": "linux64",
        "amd64": "linux64",
        "aarch64": "linux-aarch64",
        "arm64": "linux-aarch64",
    }

    INSTALL_PREFIX = Path("/opt/firefox")
    FIREFOX_BIN = INSTALL_PREFIX / "firefox"
    SYMLINK_PATH = Path("/usr/local/bin/firefox")
    DESKTOP_FILE_PATH = Path("/usr/share/applications/firefox-custom.desktop")

    def __init__(
        self,
        distro: DistroDetector,
        lang: str = "en-US",
        channel: str = "general",
        arch: str | None = None,
        migrate_data: bool = True,
        strict_security: bool = False,
        report_file: str | None = None,
    ) -> None:
        self.distro = distro
        self.lang = lang
        self.channel = channel.lower()
        self.migrate_data = migrate_data
        self.strict_security = strict_security
        self.reporter = InstallReporter(report_file=report_file)

        if self.channel not in self.CHANNEL_PRODUCT_MAP:
            valid_channels = ", ".join(sorted(self.CHANNEL_PRODUCT_MAP))
            raise ValueError(f"Unsupported Firefox channel: {channel}. Supported: {valid_channels}")

        self.arch_machine, self.os_param = self.resolve_architecture(arch)
        product = self.CHANNEL_PRODUCT_MAP[self.channel]
        self.download_url = (
            f"https://download.mozilla.org/?product={product}&os={self.os_param}&lang={self.lang}"
        )
        self.resolved_download_url = ""
        self.temp_dir: str | None = None

    def _record(self, severity: str, message: str) -> None:
        self.reporter.add(severity, message)
        if severity == "CRITICAL":
            logger.critical(message)
        elif severity == "ERROR":
            logger.error(message)
        elif severity == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

    @classmethod
    def resolve_architecture(cls, arch: str | None = None) -> tuple[str, str]:
        """Resolve machine architecture to Mozilla download `os=` parameter."""
        machine = (arch or platform.machine()).lower().strip()
        if machine not in cls.ARCH_OS_MAP:
            valid_arches = ", ".join(sorted(set(cls.ARCH_OS_MAP)))
            raise RuntimeError(
                f"Unsupported architecture: {machine}. Supported: {valid_arches}."
            )
        return machine, cls.ARCH_OS_MAP[machine]

    @staticmethod
    def require_root() -> None:
        if os.geteuid() != 0:
            raise PermissionError("This command must be run with sudo/root privileges")

    def remove_installed_firefox(self) -> None:
        self._record("INFO", f"Removing package-managed Firefox for {self.distro}")
        cmd = self.distro.get_remove_command()
        self._record("INFO", f"Running package-manager command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=self.SAFE_EXEC_ENV,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            self._record("WARNING", f"Removal returned code {result.returncode}. {stderr}")
        else:
            self._record("INFO", "Firefox package removed successfully")

    @classmethod
    def _validate_download_source(cls, response_url: str) -> None:
        parsed = urlparse(response_url)
        if parsed.scheme != "https":
            raise RuntimeError(f"Refusing non-HTTPS download URL: {response_url}")

        hostname = (parsed.hostname or "").lower()
        if hostname not in cls.ALLOWED_DOWNLOAD_HOSTS:
            allowed = ", ".join(sorted(cls.ALLOWED_DOWNLOAD_HOSTS))
            raise RuntimeError(
                f"Refusing download from untrusted host '{hostname}'. Allowed hosts: {allowed}"
            )

    def download_firefox(self) -> Path:
        self.temp_dir = tempfile.mkdtemp(prefix="firefox_install_")
        tar_path = Path(self.temp_dir) / "firefox.tar.bz2"

        self._record("INFO", "Downloading Firefox from Mozilla")
        self._record("INFO", f"Requested URL: {self.download_url}")

        req = urllib.request.Request(
            self.download_url,
            headers={"User-Agent": "firefox-installer-app"},
        )
        downloaded = 0
        with urllib.request.urlopen(req, timeout=self.DOWNLOAD_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            self._validate_download_source(final_url)
            self.resolved_download_url = final_url
            self._record("INFO", f"Resolved download URL: {final_url}")

            with tar_path.open("wb") as out:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if downloaded % (5 * 1024 * 1024) <= len(chunk):
                        self._record("INFO", f"Downloaded {downloaded / (1024 * 1024):.1f}MB")

        if tar_path.stat().st_size == 0:
            raise RuntimeError("Downloaded archive is empty")

        self._record("INFO", f"Firefox downloaded to {tar_path}")
        return tar_path

    @staticmethod
    def _compute_sha256(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_download_integrity(self, tar_path: Path) -> None:
        if not self.resolved_download_url:
            raise RuntimeError("Resolved download URL is unavailable for integrity verification")

        parsed = urlparse(self.resolved_download_url)
        file_name = Path(parsed.path).name
        if not file_name:
            raise RuntimeError("Could not determine downloaded archive filename")

        checksums_url = self.resolved_download_url.rsplit("/", 1)[0] + "/SHA256SUMS"
        self._validate_download_source(checksums_url)

        self._record("INFO", f"Verifying checksum using {checksums_url}")

        expected_sha = ""
        try:
            req = urllib.request.Request(
                checksums_url,
                headers={"User-Agent": "firefox-installer-app"},
            )
            with urllib.request.urlopen(req, timeout=self.DOWNLOAD_TIMEOUT_SECONDS) as response:
                data = response.read().decode("utf-8", errors="replace")
            for line in data.splitlines():
                line = line.strip()
                if not line or file_name not in line:
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[-1].lstrip("*") == file_name:
                    expected_sha = parts[0].lower()
                    break
        except Exception as exc:  # pylint: disable=broad-exception-caught
            msg = f"Checksum retrieval failed: {exc}"
            if self.strict_security:
                raise RuntimeError(msg) from exc
            self._record("WARNING", msg)
            return

        if not expected_sha:
            msg = f"No checksum entry found for {file_name} in SHA256SUMS"
            if self.strict_security:
                raise RuntimeError(msg)
            self._record("WARNING", msg)
            return

        actual_sha = self._compute_sha256(tar_path)
        if actual_sha != expected_sha:
            raise RuntimeError(
                f"Checksum mismatch for {file_name}. expected={expected_sha} actual={actual_sha}"
            )

        self._record("INFO", f"Checksum verified for {file_name}: {actual_sha}")

    @staticmethod
    def _download_progress(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size <= 0:
            return
        if downloaded % (5 * 1024 * 1024) == 0:
            logger.info(
                "Downloaded %.1fMB / %.1fMB",
                downloaded / (1024 * 1024),
                total_size / (1024 * 1024),
            )

    def extract_firefox(self, tar_path: Path) -> Path:
        self._record("INFO", "Extracting Firefox archive")
        if not self.temp_dir:
            raise RuntimeError("Temporary directory was not initialized")

        base_dir = Path(self.temp_dir).resolve()
        with tarfile.open(tar_path, "r:bz2") as tar:
            for member in tar.getmembers():
                member_path = base_dir / member.name
                resolved_member_path = member_path.resolve(strict=False)
                if resolved_member_path != base_dir and not str(resolved_member_path).startswith(
                    f"{base_dir}{os.sep}"
                ):
                    raise RuntimeError(f"Unsafe archive path entry rejected: {member.name}")
                if member.issym() or member.islnk():
                    raise RuntimeError(f"Archive link entry rejected: {member.name}")
                if member.isdev():
                    raise RuntimeError(f"Archive device entry rejected: {member.name}")

            tar.extractall(path=self.temp_dir)

        extract_dir = Path(self.temp_dir) / "firefox"
        if not extract_dir.exists():
            raise RuntimeError("Firefox directory not found after extraction")
        return extract_dir

    def install_firefox(self, extract_dir: Path) -> None:
        self._record("INFO", f"Installing Firefox to {self.INSTALL_PREFIX}")
        if self.INSTALL_PREFIX.exists():
            shutil.rmtree(self.INSTALL_PREFIX)
        shutil.move(str(extract_dir), str(self.INSTALL_PREFIX))

    def create_symlink(self) -> None:
        self._record("INFO", f"Creating symlink at {self.SYMLINK_PATH}")
        if self.SYMLINK_PATH.exists() or self.SYMLINK_PATH.is_symlink():
            self.SYMLINK_PATH.unlink()
        self.SYMLINK_PATH.symlink_to(self.FIREFOX_BIN)

    def create_desktop_file(self) -> None:
        self._record("INFO", f"Creating desktop entry at {self.DESKTOP_FILE_PATH}")
        desktop_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=Firefox
Exec=/opt/firefox/firefox %u
Icon=firefox
Categories=Network;WebBrowser;
Terminal=false
MimeType=text/html;text/xml;application/xhtml+xml;application/vnd.mozilla.xul+xml;text/mml;
StartupNotify=true
Keywords=web;browser;internet;www;
"""
        self.DESKTOP_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.DESKTOP_FILE_PATH.write_text(desktop_content, encoding="utf-8")
        os.chmod(self.DESKTOP_FILE_PATH, 0o644)

    def verify_installation(self) -> bool:
        self._record("INFO", "Verifying Firefox installation")
        result = subprocess.run(
            [str(self.FIREFOX_BIN), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            self._record("INFO", f"Firefox verified: {result.stdout.strip()}")
            return True
        self._record("ERROR", f"Verification failed: {result.stderr.strip()}")
        return False

    def uninstall(self) -> None:
        self.require_root()
        if self.INSTALL_PREFIX.exists():
            self._record("INFO", f"Removing {self.INSTALL_PREFIX}")
            shutil.rmtree(self.INSTALL_PREFIX)
        if self.SYMLINK_PATH.exists() or self.SYMLINK_PATH.is_symlink():
            self._record("INFO", f"Removing {self.SYMLINK_PATH}")
            self.SYMLINK_PATH.unlink()
        if self.DESKTOP_FILE_PATH.exists():
            self._record("INFO", f"Removing {self.DESKTOP_FILE_PATH}")
            self.DESKTOP_FILE_PATH.unlink()

    def cleanup(self) -> None:
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @staticmethod
    def _resolve_target_user() -> tuple[str, Path, int, int]:
        """Return target username/home/uid/gid for profile migration."""
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user:
            pw = pwd.getpwnam(sudo_user)
            return sudo_user, Path(pw.pw_dir), pw.pw_uid, pw.pw_gid

        uid = os.getuid()
        gid = os.getgid()
        username = pwd.getpwuid(uid).pw_name
        return username, Path.home(), uid, gid

    @staticmethod
    def _chown_recursive(path: Path, uid: int, gid: int) -> None:
        """Ensure migrated files are owned by the target user."""
        os.chown(path, uid, gid)
        for root, dirs, files in os.walk(path):
            for name in dirs:
                os.chown(Path(root) / name, uid, gid)
            for name in files:
                os.chown(Path(root) / name, uid, gid)

    def migrate_profile_data(self) -> None:
        """Migrate Firefox profile data from Snap/Flatpak into ~/.mozilla/firefox."""
        username, home_dir, uid, gid = self._resolve_target_user()
        target_profile_root = home_dir / ".mozilla" / "firefox"

        # Preserve existing native profiles; migration is only needed when target is absent.
        if target_profile_root.exists():
            self._record("INFO", f"Profile data already present at {target_profile_root}; skipping migration")
            return

        migration_sources = [
            ("snap", home_dir / "snap" / "firefox" / "common" / ".mozilla" / "firefox"),
            ("snap-current", home_dir / "snap" / "firefox" / "current" / ".mozilla" / "firefox"),
            ("flatpak", home_dir / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox"),
        ]

        for source_name, source_path in migration_sources:
            if not source_path.exists() or not source_path.is_dir():
                continue
            if not any(source_path.iterdir()):
                continue

            has_symlink = False
            for root, dirs, files in os.walk(source_path):
                for name in dirs + files:
                    if (Path(root) / name).is_symlink():
                        logger.warning(
                            "Skipping %s migration due to symlinked entry in source profile: %s",
                            source_name,
                            Path(root) / name,
                        )
                        if self.strict_security:
                            raise RuntimeError(
                                f"Symlinked entry found in migration source {source_name}: {Path(root) / name}"
                            )
                        has_symlink = True
                        break
                if has_symlink:
                    break
            if has_symlink:
                continue

            self._record(
                "INFO",
                (
                    f"Migrating Firefox profile data for user {username} "
                    f"from {source_name} path: {source_path}"
                ),
            )
            target_profile_root.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_path, target_profile_root)

            self._chown_recursive(target_profile_root, uid, gid)
            self._record("INFO", f"Profile migration completed: {target_profile_root}")
            return

        self._record("INFO", "No Snap/Flatpak Firefox profile data found for migration")

    def install(self) -> bool:
        self.require_root()
        ok = False
        try:
            self._record("INFO", "=" * 60)
            self._record("INFO", "Firefox Installer from Source")
            self._record("INFO", f"Detected OS: {self.distro}")
            self._record("INFO", f"Architecture: {self.arch_machine} ({self.os_param})")
            self._record("INFO", f"Release channel: {self.channel}")
            self._record("INFO", f"Strict security mode: {'enabled' if self.strict_security else 'disabled'}")
            self._record("INFO", "=" * 60)

            self.remove_installed_firefox()
            tar_path = self.download_firefox()
            self.verify_download_integrity(tar_path)
            extract_dir = self.extract_firefox(tar_path)
            self.install_firefox(extract_dir)
            self.create_symlink()
            self.create_desktop_file()
            if self.migrate_data:
                self.migrate_profile_data()
            else:
                self._record("INFO", "Profile migration disabled by flag")
            ok = self.verify_installation()
            if ok:
                self._record("INFO", "Installation completed successfully")
            else:
                self._record("ERROR", "Installation completed with verification failure")
            return ok
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._record("CRITICAL", f"Installation failed: {exc}")
            return False
        finally:
            self.cleanup()
            self.reporter.print_report()
            self.reporter.write_report_file()


def run_readiness_checks() -> int:
    """Run basic preflight checks and return a process exit code."""
    print("=" * 60)
    print("Firefox Installation Readiness Checker")
    print("=" * 60)

    print("\nRoot:")
    print("  OK" if os.geteuid() == 0 else "  Not root (sudo will be required for install)")

    print("\nPython:")
    print(f"  {os.sys.version.split()[0]}")

    print("\nDistribution:")
    try:
        distro = DistroDetector()
        print(f"  {distro} (supported)")
    except Exception as exc:
        print(f"  Unsupported: {exc}")
        return 1

    print("\nDisk Space:")
    stat = os.statvfs("/opt" if Path("/opt").exists() else "/")
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024 * 1024)
    print(f"  {free_gb:.2f} GB free")

    print("\nStatus: READY")
    return 0
