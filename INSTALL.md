# Installation Guide

This guide reflects the current 1.0.0 layout: a Python CLI app, compatibility wrappers for the original scripts, and local automation helpers for packaging and release tasks.

## Prerequisites

- Linux operating system
- Root or sudo access for install and uninstall operations
- Python 3.8 or higher
- Internet access
- About 600MB of free disk space

## Recommended Workflow

1. Check readiness:
   ```bash
   python3 check_readiness.py
   ```
2. Detect what the installer sees on your system:
   ```bash
   python3 install_firefox.py detect
   ```
3. Install Firefox from Mozilla binaries:
   ```bash
   sudo ./install.sh
   ```
4. Verify the installed browser:
   ```bash
   firefox --version
   ```

The wrapper script defaults to the `install` command and will elevate with `sudo` when needed.

## Available Entry Points

### Wrapper Script

Use the shell wrapper if you want the original repo-local workflow:

```bash
sudo ./install.sh
./install.sh --version
./install.sh check
./install.sh detect
sudo ./install.sh uninstall
```

### Compatibility Python Script

Use the legacy script name if you have automation that still calls it:

```bash
sudo python3 install_firefox.py install
python3 install_firefox.py check
python3 install_firefox.py detect
sudo python3 install_firefox.py uninstall
```

### Installed CLI App

Install the project once and use the command globally:

```bash
python3 -m pip install .
```

Then run:

```bash
firefox-installer check
firefox-installer detect
sudo firefox-installer install
sudo firefox-installer install --channel beta
sudo firefox-installer install --channel esr --arch arm64
sudo firefox-installer uninstall
firefox-installer --version
```

Supported channel values:
- `general`
- `beta`
- `nightly`
- `developer`
- `esr`

Supported `--arch` values:
- `auto` (default; detect from current machine)
- `x86_64`
- `arm64`

Data migration control:
- Automatic by default (Snap/Flatpak profiles into `~/.mozilla/firefox` when target profile is missing)
- Disable with `--no-migrate-data`

Example:

```bash
sudo firefox-installer install --channel esr --arch arm64 --no-migrate-data
```

Security and reporting controls:
- `--strict-security`: fail installation on checksum/migration anomalies
- `--report-file <path>`: write structured JSON report with `INFO`, `WARNING`, `ERROR`, `CRITICAL` events

Example:

```bash
sudo firefox-installer install --strict-security --report-file /var/log/firefox-installer-report.json
```

## What the Installer Changes

Successful installation creates:

- `/opt/firefox/`
- `/usr/local/bin/firefox`
- `/usr/share/applications/firefox-custom.desktop`

The installer also removes a package-managed Firefox package for supported distros before installing Mozilla's upstream binary build.

## Supported Distributions

- Ubuntu and Debian family via `apt`
- Fedora via `dnf`
- CentOS and RHEL via `yum`
- Arch and Manjaro via `pacman`
- openSUSE via `zypper`
- Alpine via `apk`

If your exact distro ID is not listed but `ID_LIKE` maps to one of the supported families, detection still works.

## Local Package Builds

This repo can build local artifacts for distribution and testing.

### Debian Package

```bash
make package-deb
```

Output:
- `dist/firefox-installer_<version>_<arch>.deb`

### RPM Package

```bash
make package-rpm
```

Requirements:
- `rpmbuild`

### AUR Bundle

```bash
make package-aur
```

Output:
- `dist/aur/PKGBUILD`
- `dist/aur/firefox-installer-<version>.tar.gz`

### Build Everything

```bash
make package-all
```

## Artifact Validation And Signing

Smoke-test the generated artifacts:

```bash
bash automation/test_packages.sh
```

Create detached GPG signatures and a SHA256 manifest:

```bash
bash automation/sign_packages.sh
```

Use a specific signing key:

```bash
bash automation/sign_packages.sh YOUR_KEY_ID
```

## Troubleshooting

### Python Is Missing

Install Python 3 with your distro package manager, then retry the command.

### Installer Says Root Is Required

Run the install or uninstall command with `sudo`. Readiness and detection commands can run unprivileged.

### Download Or Verification Fails

Retry with verbose logging:

```bash
sudo python3 install_firefox.py --verbose install
```

Capture logs if needed:

```bash
sudo python3 install_firefox.py --verbose install 2>&1 | tee firefox_debug.log
```

### Unsupported Distribution

Check your distro identifiers:

```bash
grep -E '^(ID|ID_LIKE|NAME|VERSION_ID)=' /etc/os-release
```

To add support, update `DistroDetector.DISTROS` in `src/firefox_installer_app/core.py`.

### Firefox Will Not Start

Check the installed binary directly:

```bash
/opt/firefox/firefox --version
```

If runtime libraries are missing, install the GTK and DBus packages for your distro and retry.

## Uninstall

Use one of the supported entry points instead of manually deleting files:

```bash
sudo ./install.sh uninstall
sudo python3 install_firefox.py uninstall
sudo firefox-installer uninstall
```

## Developer Notes

- CLI wiring lives in `src/firefox_installer_app/cli.py`
- Distro detection and install logic live in `src/firefox_installer_app/core.py`
- `install_firefox.py` and `check_readiness.py` are compatibility wrappers
- Packaging templates live under `packaging/`

## License

The installer code in this repository is MIT-licensed. Firefox itself remains licensed under the Mozilla Public License 2.0.
