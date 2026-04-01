# Quick Start Guide

## Installation in 30 Seconds

1. **Check your system is ready**:
   ```bash
   python3 check_readiness.py
   ```

2. **Optionally confirm distro detection**:
   ```bash
   python3 install_firefox.py detect
   ```

3. **Run the installer**:
   ```bash
   sudo ./install.sh
   ```

   Optional app install:
   ```bash
   python3 -m pip install .
   firefox-installer check
   sudo firefox-installer install
   sudo firefox-installer install --channel beta
   sudo firefox-installer install --strict-security --report-file ./firefox-install-report.json
   ```

4. **Done!** Launch Firefox:
   ```bash
   firefox
   ```

---

## That's It!

The installer will:
- ✓ Detect your Linux distribution
- ✓ Remove existing Firefox packages
- ✓ Download latest Firefox from Mozilla
- ✓ Install to `/opt/firefox`
- ✓ Create system shortcuts
- ✓ Migrate existing Snap/Flatpak profile data when needed
- ✓ Verify the installation

**Total time**: ~3-5 minutes (depends on internet speed)

---

## Troubleshooting

### "Permission denied" or "sudo: command not found"
```bash
# Make the shell entrypoint executable first
chmod +x install.sh

# Then run with sudo
sudo ./install.sh
```

If you prefer the Python entrypoint instead:

```bash
sudo python3 install_firefox.py install
```

### Script stuck downloading
Firefox is large (~150-200MB). If it takes too long:
- Check your internet speed
- Try again after a few minutes
- Mozilla's servers might be busy

### Firefox won't open after installation
Try running directly:
```bash
/opt/firefox/firefox &
```

If that fails, check dependencies:
```bash
# Ubuntu/Debian
sudo apt install libgtk-3-0 libdbus-glib-1-2

# Fedora
sudo dnf install gtk3 dbus-glib
```

---

## What Got Installed

After successful installation, you have:

| Path | Purpose |
|------|---------|
| `/opt/firefox/` | Main Firefox installation |
| `/usr/local/bin/firefox` | Command-line shortcut |
| `~/.mozilla/firefox/` | Your Firefox profiles & settings |

---

## Next Steps

- **First launch**: Click the Firefox icon or run `firefox`
- **Restore settings**: Import from your previous Firefox installation
- **Extensions**: Install your favorite add-ons from Firefox Add-ons store
- **Sync**: Sign in with Mozilla account to sync bookmarks, history, tabs

---

## Update Firefox

To get the latest version anytime:
```bash
sudo ./install.sh
# or, if installed as app
sudo firefox-installer install
```

It will replace your current installation.

---

## Uninstall

Remove Firefox completely:
```bash
sudo ./install.sh uninstall
# or, if installed as app
sudo firefox-installer uninstall
```

---

## Package Builds

Generate local distro artifacts:

```bash
make package-deb
make package-aur
```

Smoke-test the generated artifacts:

```bash
bash automation/test_packages.sh
```

---

## More Help

See [README.md](README.md) for comprehensive documentation.
