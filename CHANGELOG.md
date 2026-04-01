# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project follows Semantic Versioning.

## [1.0.0] - 2026-03-30

### Added

- Installable Python CLI app with `install`, `uninstall`, `check`, and `detect` commands.
- Multi-distro support with package-manager cleanup and distro detection via `/etc/os-release`.
- Direct Firefox installation from Mozilla binaries with verification and system integration.
- Install-time options for locale, release channel, architecture, and Snap/Flatpak profile migration.
- Security hardening for download validation, archive handling, and strict failure mode.
- Structured JSON reporting (`--report-file`) and local packaging helpers for DEB, RPM, and AUR workflows.
