#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Built with Google Antigravity
set -euo pipefail

PKG_NAME="adb-auto"
VERSION="1.3.1"
ARCH="all"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
STAGE_ROOT="/tmp/${PKG_NAME}-build-$$"
DEB_ROOT="$STAGE_ROOT/${PKG_NAME}_${VERSION}_${ARCH}"

# Enforce Debian Reproducible Builds via SOURCE_DATE_EPOCH
if [ -f "$PROJECT_DIR/debian/changelog" ]; then
    export SOURCE_DATE_EPOCH="$(dpkg-parsechangelog -l "$PROJECT_DIR/debian/changelog" -STimestamp)"
fi

rm -rf "$STAGE_ROOT"
mkdir -p "$DIST_DIR"

# Stage Debian Package (.deb) on /tmp (for strict 0755/0644 POSIX permissions)
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/usr/share/man/man1"
mkdir -p "$DEB_ROOT/usr/share/doc/$PKG_NAME"

cat > "$DEB_ROOT/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Section: devel
Priority: optional
Architecture: $ARCH
Depends: python3, adb, iproute2, iputils-ping
Homepage: https://github.com/Aryston/adb-auto
Maintainer: Igor Jagec <igor.jagec@gmail.com>
Description: Connect Googlebook Linux terminal to Android Wireless Debugging
 Minimalist CLI tool that connects the Debian Linux VM on a Googlebook
 (Android Laptop) to the local Android Host over Wireless Debugging
 without manual IP address or random port lookups.
 .
 Vibe-coded and engineered with Google Antigravity. Licensed under GPL-2.0.
EOF

cat > "$DEB_ROOT/usr/share/doc/$PKG_NAME/copyright" <<EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: adb-auto
Source: https://github.com/Aryston/adb-auto

Files: *
Copyright: 2026 Igor Jagec <igor.jagec@gmail.com>, vibe-coded with Google Antigravity
License: GPL-2.0-only
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; version 2 of the License.
 .
 On Debian systems, the complete text of the GNU General Public
 License version 2 can be found in "/usr/share/common-licenses/GPL-2".
EOF

install -m 0755 "$PROJECT_DIR/adb_auto.py" "$DEB_ROOT/usr/bin/adb-auto"
gzip -9 -n -c "$PROJECT_DIR/man/adb-auto.1" > "$DEB_ROOT/usr/share/man/man1/adb-auto.1.gz"
chmod 0644 "$DEB_ROOT/usr/share/man/man1/adb-auto.1.gz"

if [ -f "$PROJECT_DIR/debian/changelog" ]; then
    gzip -9 -n -c "$PROJECT_DIR/debian/changelog" > "$DEB_ROOT/usr/share/doc/$PKG_NAME/changelog.gz"
    chmod 0644 "$DEB_ROOT/usr/share/doc/$PKG_NAME/changelog.gz"
fi

install -m 0644 "$PROJECT_DIR/README.md" "$DEB_ROOT/usr/share/doc/$PKG_NAME/README.md"
chmod 0644 "$DEB_ROOT/usr/share/doc/$PKG_NAME/copyright"

find "$DEB_ROOT" -type d -exec chmod 0755 {} +
chmod 0644 "$DEB_ROOT/DEBIAN/control"

# Generate md5sums control file
(cd "$DEB_ROOT" && find * -type f ! -path 'DEBIAN/*' -exec md5sum {} + > "$DEB_ROOT/DEBIAN/md5sums")
chmod 0644 "$DEB_ROOT/DEBIAN/md5sums"

# Clamp all timestamps to SOURCE_DATE_EPOCH for reproducible builds
if [ -n "${SOURCE_DATE_EPOCH:-}" ]; then
    find "$DEB_ROOT" -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
fi

DEB_OUT="$DIST_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --root-owner-group --build "$DEB_ROOT" "$DEB_OUT"

rm -rf "$STAGE_ROOT"

echo "==================================================="
echo "[✓] Built Debian package : $DEB_OUT"
echo "==================================================="
ls -lh "$DEB_OUT"
