SHELL := /bin/bash

APP_NAME := firefox-installer
OUT_DIR := dist

.PHONY: help install-dev build-wheel build-sdist package-deb package-rpm package-aur package-all validate-rpm-local clean

help:
	@echo "Available targets:"
	@echo "  install-dev  - install app in editable mode"
	@echo "  build-wheel  - build Python wheel"
	@echo "  build-sdist  - build Python source distribution"
	@echo "  package-deb  - build Debian package (.deb)"
	@echo "  package-rpm  - build RPM package (.rpm)"
	@echo "  package-aur  - generate AUR PKGBUILD bundle"
	@echo "  package-all  - build deb, rpm, and aur artifacts"
	@echo "  validate-rpm-local - build and smoke-test the RPM locally when rpm tools are installed"
	@echo "  clean        - remove build artifacts"

install-dev:
	python3 -m pip install -e .

build-wheel:
	python3 -m pip install --quiet build
	python3 -m build --wheel

build-sdist:
	python3 -m pip install --quiet build
	python3 -m build --sdist

package-deb:
	./automation/package_deb.sh

package-rpm:
	./automation/package_rpm.sh

package-aur:
	./automation/package_aur.sh

package-all: package-deb package-rpm package-aur

validate-rpm-local:
	./automation/validate_rpm_local.sh

clean:
	rm -rf $(OUT_DIR) build *.egg-info src/*.egg-info .pytest_cache __pycache__ src/firefox_installer_app/__pycache__
