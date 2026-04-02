```
⠀⠀⠀⠀⠀⠀⢱⣆⠀⠀⠀⠀⠀⠀   
⠀⠀⠀⠀⠀⠀⠈⣿⣷⡀⠀⠀⠀⠀     █████▒██▀███  ▓█████   ██████  ██░ ██ 
⠀⠀⠀⠀⠀⠀⢸⣿⣿⣷⣧⠀⠀⠀   ▓██   ▒▓██ ▒ ██▒▓█   ▀ ▒██    ▒ ▓██░ ██▒
⠀⠀⠀⠀⡀⢠⣿⡟⣿⣿⣿⡇⠀⠀   ▒████ ░▓██ ░▄█ ▒▒███   ░ ▓██▄   ▒██▀▀██░
⠀⠀⠀⠀⣳⣼⣿⡏⢸⣿⣿⣿⢀⠀   ░▓█▒  ░▒██▀▀█▄  ▒▓█  ▄   ▒   ██▒░▓█ ░██ 
⠀⠀⠀⣰⣿⣿⡿⠁⢸⣿⣿⡟⣼⡆   ░▒█░   ░██▓ ▒██▒░▒████▒▒██████▒▒░▓█▒░██▓
⢰⢀⣾⣿⣿⠟⡀⠀⣾⢿⣿⣿⣿⣿    ▒ ░   ░ ▒▓ ░▒▓░░░ ▒░ ░▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒
⢸⣿⣿⣿⡏⠀⠀⠀⠃⠸⣿⣿⣿⡿    ░       ░▒ ░ ▒░ ░ ░  ░░ ░▒  ░ ░ ▒ ░▒░ ░
⢳⣿⣿⣿⠀⠀⠀⠀⠀⠀⢹⣿⡿⡁    ░ ░     ░░   ░    ░   ░  ░  ░   ░  ░░ ░
⠀⠹⣿⣿⡄⠀⠀⠀⠀⠀⢠⣿⡞⠁             ░        ░  ░      ░   ░  ░  ░
⠀⠀⠈⠛⢿⣄⠀⠀⠀⣠⠞⠋⠀⠀                                # Firefresh
⠀⠀⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠀⠀   
```

# Firefox Source Installer for Linux

A fully automated application that removes package-managed Firefox and installs the latest Firefox directly from Mozilla's official source on Linux systems.

Current version: `1.0.0`

## Features

- **Automatic Distribution Detection**: Identifies your Linux distro and uses appropriate package managers
- **Clean Removal**: Removes existing Firefox installation using distro-specific package managers
- **Direct Source Installation**: Downloads and installs Firefox directly from Mozilla
- **System Integration**: Creates symlinks and desktop integration for system-wide access
- **Comprehensive Logging**: Detailed output of all operations
- **Error Handling**: Graceful error handling with informative messages

## Supported Distributions

- **Debian-based**: Ubuntu, Debian
- **Red Hat-based**: Fedora, CentOS, RHEL
- **Arch-based**: Arch Linux, Manjaro
- **Other**: openSUSE, Alpine Linux

## Requirements

- Linux operating system
- Root/sudo access
- Python 3.8+
- Internet connection for downloading Firefox
- ~600MB free disk space (~250MB for Firefox + temporary files)

## Installation

### Quick Start

1. **Clone or download this repository**:
   ```bash
   cd /path/to/firefox_installer
   ```

2. **Run the installer**:
   ```bash
   sudo ./install.sh
   ```

   Or directly with Python:
   ```bash
   sudo python3 install_firefox.py
   ```

### Install As an App (CLI)

Install this project as a local Python application:

```bash
python3 -m pip install .
```

Then use the command from anywhere:

```bash
firefox-installer check
firefox-installer detect
sudo firefox-installer install
sudo firefox-installer install --channel beta
sudo firefox-installer install --channel esr --arch arm64
```

### Build Distro Packages Locally

Generate local package artifacts without publishing:

```bash
make package-deb
make package-rpm
make package-aur
```

Build all package types:

```bash
make package-all
```

Artifacts are written to `dist/`.

### Step-by-Step

1. Extract the repository to a directory of your choice
2. Open a terminal and navigate to the directory
3. Make the script executable (if needed):
   ```bash
   chmod +x install.sh
   chmod +x install_firefox.py
   ```
4. Run with sudo:
   ```bash
   sudo ./install.sh
   ```

## What the Installer Does

1. **Detects your Linux distribution** using `/etc/os-release`
2. **Removes existing Firefox**:
   - Uses `apt` for Debian/Ubuntu
   - Uses `dnf` for Fedora
   - Uses `yum` for CentOS/RHEL
   - Uses `pacman` for Arch/Manjaro
   - Uses `zypper` for openSUSE
   - Uses `apk` for Alpine
3. **Downloads Firefox** directly from Mozilla's CDN
4. **Extracts and installs** to `/opt/firefox`
5. **Creates symlink** at `/usr/local/bin/firefox` for system-wide access
6. **Sets up desktop integration** for application menus
7. **Migrates user data** from Snap/Flatpak Firefox profiles into `~/.mozilla/firefox` when needed
8. **Verifies the installation** by checking Firefox version

## Usage

Available app commands:

```bash
firefox-installer check
firefox-installer detect
sudo firefox-installer install
sudo firefox-installer uninstall
firefox-installer --version
```

`install` supports channel and architecture options:

```bash
sudo firefox-installer install --channel general
sudo firefox-installer install --channel beta
sudo firefox-installer install --channel nightly
sudo firefox-installer install --channel developer
sudo firefox-installer install --channel esr
sudo firefox-installer install --arch auto
sudo firefox-installer install --arch x86_64
sudo firefox-installer install --arch arm64
```

After installation, simply run:

```bash
firefox
```

Or from anywhere:

```bash
/opt/firefox/firefox
```

Firefox will also appear in your application menu (depending on your desktop environment).

### Check Installer Version

```bash
./install.sh --version
```

Or:

```bash
firefox-installer --version
```

## Installation Paths

- **Main Installation**: `/opt/firefox/`
- **Executable**: `/opt/firefox/firefox`
- **Symlink**: `/usr/local/bin/firefox`
- **Desktop File**: `/usr/share/applications/firefox-custom.desktop`

## Troubleshooting

### Script requires sudo
The installer needs root privileges to remove packages and install system-wide. This is expected and normal.

### "Unsupported distribution" error
Your Linux distribution is not currently supported. You can manually add support by:
1. Finding your distro ID by running: `grep ^ID= /etc/os-release`
2. Adding it to the `DistroDetector.DISTROS` mapping in `src/firefox_installer_app/core.py`
3. Submitting a PR or issue with the distro details

### Download fails
- Check your internet connection
- Mozilla's download servers might be slow; retry after a few moments
- Try increasing the timeout by editing the timeout parameter in the code

### Firefox won't start
- Ensure all dependencies are installed: `sudo apt install libgtk-3-0` (for Debian/Ubuntu)
- Check `/opt/firefox/firefox --version` works
- Review the installation logs for errors

### Port already in use
If Firefox fails to start due to an existing instance:
```bash
pkill -9 firefox
```

## Advanced Options

### Language Selection
Install Firefox with a specific locale:

```bash
sudo firefox-installer install --lang=de
```

### Release Channel Selection
Install a specific Firefox channel:

```bash
sudo firefox-installer install --channel general
sudo firefox-installer install --channel beta
sudo firefox-installer install --channel nightly
sudo firefox-installer install --channel developer
sudo firefox-installer install --channel esr
```

### Architecture Selection
By default, architecture is auto-detected from your machine. Override it manually if needed:

```bash
sudo firefox-installer install --arch auto
sudo firefox-installer install --arch x86_64
sudo firefox-installer install --arch arm64
```

You can combine these options:

```bash
sudo firefox-installer install --channel esr --arch arm64 --lang=de
```

### Security Mode And Reporting
Enable stricter security behavior during install:

```bash
sudo firefox-installer install --strict-security
```

In strict mode, install fails on checksum retrieval/validation issues and migration anomalies.

Write a structured JSON install report (including `INFO`, `WARNING`, `ERROR`, `CRITICAL` events):

```bash
sudo firefox-installer install --report-file /var/log/firefox-installer-report.json
```

You can combine both:

```bash
sudo firefox-installer install --strict-security --report-file /var/log/firefox-installer-report.json
```

### Snap/Flatpak Data Migration
During install, the app automatically checks for profile data in these locations and migrates it to `~/.mozilla/firefox` if that target directory does not already exist:

- `~/snap/firefox/common/.mozilla/firefox`
- `~/snap/firefox/current/.mozilla/firefox`
- `~/.var/app/org.mozilla.firefox/.mozilla/firefox`

Disable migration if you prefer a clean profile:

```bash
sudo firefox-installer install --no-migrate-data
```

### Specify Older Firefox Version
The installer downloads the latest version. For specific versions, visit:
https://www.mozilla.org/firefox/releases/

Then manually download and extract to your preferred location.

## Updating Firefox

To update Firefox to the latest version, simply run the installer again:
```bash
sudo ./install.sh
# or
sudo firefox-installer install
```

It will replace the existing installation with the newest version.

## Uninstalling

To completely remove Firefox installed by this app:

```bash
sudo ./install.sh uninstall
# or
sudo firefox-installer uninstall
```

## Logs and Debugging

The installer outputs detailed logs and a final severity-based report to the console. For debugging:

1. Run with output capture:
   ```bash
   sudo python3 install_firefox.py install 2>&1 | tee firefox_install.log
   ```

2. Check the generated log file `firefox_install.log` for any errors

## System Requirements by Distro

### Ubuntu/Debian
```bash
# These are automatically handled by the installer
sudo apt install libgtk-3-0 libdbus-glib-1-2
```

### Fedora
```bash
# Automatically handled by the installer
sudo dnf install gtk3 dbus-glib
```

### Arch
```bash
# Usually no extra dependencies needed
```

## Security Considerations

- This script modifies your system and requires root access
- Firefox is downloaded from Mozilla's official servers (secure HTTPS)
- Desktop files created are standard and follow freedesktop.org specifications
- No telemetry or tracking is added by this installer

## Compatibility

- **OS**: Linux (all major distributions)
- **Architecture**: x86_64 (64-bit)
- **Python**: 3.8 or higher
- **Desktop Environments**: Works with GNOME, KDE, Xfce, and others

## License

This project is licensed under the MIT License. See `LICENSE` for details.

Firefox itself is licensed under the Mozilla Public License 2.0.

## Changelog

See `CHANGELOG.md` for release history.

## Contributing

To add support for additional distributions:

1. Find your distro ID: `grep ^ID= /etc/os-release`
2. Identify the package manager and Firefox removal command
3. Add an entry to `DistroDetector.DISTROS` in `src/firefox_installer_app/core.py`
4. Test thoroughly

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review Firefox logs: `~/.mozilla/firefox/`
3. Check the installer output for error messages

## Firefox Documentation

- Official Firefox: https://www.mozilla.org/firefox/
- Firefox Support: https://support.mozilla.org/
- Source Code: https://hg.mozilla.org/mozilla-central/

---

**Last Updated**: 2026-03-30
**Tested On**: Ubuntu 22.04 LTS, Fedora 38, Debian 12, Arch Linux, Manjaro
