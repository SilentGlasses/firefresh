# Project Structure

This file documents the current 1.0.0 repository layout.

## Top-Level Layout

```text
firefox_installer/
├── install.sh
├── install_firefox.py
├── check_readiness.py
├── pyproject.toml
├── README.md
├── QUICKSTART.md
├── INSTALL.md
├── CHANGELOG.md
├── Makefile
├── packaging/
├── automation/
└── src/
```

## Runtime Entry Points

### `install.sh`

- Shell wrapper for repo-local usage
- Supports `install`, `uninstall`, `check`, `detect`, and `--version`
- Elevates with `sudo` for privileged operations

### `install_firefox.py`

- Compatibility wrapper for the legacy script name
- Adds `src/` to `sys.path`
- Delegates to `firefox_installer_app.cli:main`

### `check_readiness.py`

- Compatibility wrapper for the readiness check
- Equivalent to running `python3 install_firefox.py check`

## Python Application Layout

### `src/firefox_installer_app/__init__.py`

- Defines the package version

### `src/firefox_installer_app/cli.py`

- Builds the CLI parser
- Configures logging
- Dispatches `install`, `uninstall`, `check`, and `detect`

### `src/firefox_installer_app/core.py`

- Implements distro detection from `/etc/os-release`
- Defines distro-specific package removal commands
- Downloads, extracts, installs, verifies, and uninstalls Firefox
- Contains the readiness checks

## Packaging Layout

### `packaging/common/firefox-installer-launcher`

- Shared launcher used by generated system packages

### `packaging/rpm/firefox-installer.spec.in`

- RPM spec template with version substitution

### `packaging/aur/PKGBUILD.in`

- AUR PKGBUILD template with version and SHA256 substitution

### `automation/package_deb.sh`

- Builds a local `.deb` artifact under `dist/`

### `automation/package_rpm.sh`

- Builds a local `.rpm` artifact under `dist/`
- Requires `rpmbuild`

### `automation/package_aur.sh`

- Produces an AUR tarball and rendered `PKGBUILD`

### `automation/test_packages.sh`

- Smoke-tests generated `.deb`, `.rpm`, and AUR outputs

### `automation/sign_packages.sh`

- Creates detached ASCII-armored signatures and a `SHA256SUMS` manifest

## Build And Release Files

### `pyproject.toml`

- Defines the installable Python package metadata
- Exposes the `firefox-installer` console script

### `Makefile`

- Convenience targets for editable install, wheel/sdist builds, and package generation

### `CHANGELOG.md`

- Release history through version 1.0.0

## Operational Summary

- Minimum supported Python version: 3.8
- Install target: `/opt/firefox`
- Symlink target: `/usr/local/bin/firefox`
- Desktop entry: `/usr/share/applications/firefox-custom.desktop`
- Supported distro families: Debian, Fedora, RHEL/CentOS, Arch, openSUSE, Alpine

## Quick Commands

```bash
python3 check_readiness.py
python3 install_firefox.py detect
sudo ./install.sh
python3 -m pip install .
make package-all
bash automation/test_packages.sh
```
