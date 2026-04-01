"""Command-line interface for firefox-installer app."""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .core import DistroDetector, FirefoxInstaller, run_readiness_checks


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="firefox-installer",
        description="Install Firefox from Mozilla binaries with distro-aware package removal.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="Install Firefox")
    install_parser.add_argument("--lang", default="en-US", help="Firefox locale (default: en-US)")
    install_parser.add_argument(
        "--channel",
        default="general",
        choices=["general", "beta", "nightly", "developer", "esr"],
        help="Firefox release channel (default: general)",
    )
    install_parser.add_argument(
        "--arch",
        default="auto",
        choices=["auto", "x86_64", "arm64"],
        help="CPU architecture for download selection (default: auto)",
    )
    install_parser.add_argument(
        "--no-migrate-data",
        action="store_true",
        help="Disable Snap/Flatpak profile migration into ~/.mozilla/firefox",
    )
    install_parser.add_argument(
        "--strict-security",
        action="store_true",
        help="Enable strict security checks (fail on checksum/migration anomalies)",
    )
    install_parser.add_argument(
        "--report-file",
        default=None,
        help="Write a JSON install report to this file path",
    )

    subparsers.add_parser("uninstall", help="Remove Firefox installed by this app")
    subparsers.add_parser("check", help="Run readiness checks")
    subparsers.add_parser("detect", help="Show detected distro and package manager")

    return parser


def cmd_detect() -> int:
    distro = DistroDetector()
    arch_machine, os_param = FirefoxInstaller.resolve_architecture()
    print(f"Distribution: {distro}")
    print(f"Distro ID: {distro.distro_id}")
    print(f"Package manager: {distro.get_package_manager()}")
    print(f"Architecture: {arch_machine}")
    print(f"Mozilla OS parameter: {os_param}")
    print("Channels: general, beta, nightly, developer, esr")
    return 0


def cmd_install(
    lang: str,
    channel: str,
    arch: str,
    no_migrate_data: bool,
    strict_security: bool,
    report_file: str | None,
) -> int:
    distro = DistroDetector()
    arch_override = None if arch == "auto" else arch
    installer = FirefoxInstaller(
        distro=distro,
        lang=lang,
        channel=channel,
        arch=arch_override,
        migrate_data=not no_migrate_data,
        strict_security=strict_security,
        report_file=report_file,
    )
    ok = installer.install()
    return 0 if ok else 1


def cmd_uninstall() -> int:
    distro = DistroDetector()
    installer = FirefoxInstaller(distro=distro)
    installer.uninstall()
    print("Firefox installation removed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.verbose)

    command = args.command or "install"

    try:
        if command == "install":
            return cmd_install(
                args.lang,
                args.channel,
                args.arch,
                args.no_migrate_data,
                args.strict_security,
                args.report_file,
            )
        if command == "uninstall":
            return cmd_uninstall()
        if command == "check":
            return run_readiness_checks()
        if command == "detect":
            return cmd_detect()
        parser.print_help()
        return 2
    except PermissionError as exc:
        logging.error(str(exc))
        return 1
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Fatal error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
