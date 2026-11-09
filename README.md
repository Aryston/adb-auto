# `adb-auto` — Wireless ADB Auto-Connector for Googlebook

[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Built with Google Antigravity](https://img.shields.io/badge/Vibe--Coded_with-Google_Antigravity-4285F4?logo=google)](https://deepmind.google/)

Connects the Googlebook (Android Laptop) Debian Linux terminal to Android Wireless Debugging automatically—without looking up IP addresses or random port numbers.

> **Attribution:** Conceived by [Igor (@Aryston)](https://github.com/Aryston) (with guide testing by Denny Lockhart) and vibe-coded with **Google Antigravity** (Google DeepMind). Licensed under **GNU GPL v2.0**.

![adb-auto in action on Lenovo Googlebook 15](docs/images/06-adb-auto-in-action.jpg)

---

## Prerequisite: Enable Wireless Debugging on Googlebook

`adb-auto` requires **Use wireless debugging** to be turned **ON** in Android Settings:

1. Go to **Settings -> About device** and tap **Build number** 7 times until Developer options unlock.
   ![Enable Developer Options](docs/images/01-enable-dev-options.png)
2. Go to **Settings -> System -> Developer options** and tap **Wireless debugging**.
   ![Wireless Debugging Menu](docs/images/02-wireless-debugging-menu.png)
3. Toggle on **Use wireless debugging** and accept the **Allow wireless debugging?** prompt.
   ![Allow Wireless Debugging](docs/images/03-allow-wireless-debugging.png)

> **Note on Sleep / Disconnections:** Android automatically suspends Wireless Debugging after sleep or Wi-Fi changes (sometimes showing `Unavailable (not allowed)` while the switch still looks ON). If connection fails, toggle **Use wireless debugging** OFF and back ON, then run `adb-auto`.
>
> ![Unavailable (not allowed) state](docs/images/07-unavailable-not-allowed.jpg)

---

## Installation

### Option 1: Debian Package (`.deb`) — Recommended
Automatically installs `/usr/bin/adb-auto`, the `man adb-auto` page, and required system dependencies (`adb`, `python3`, `iproute2`, `iputils-ping`) in one go:

```bash
curl -fLO https://raw.githubusercontent.com/Aryston/adb-auto/main/dist/adb-auto_1.0.0_all.deb
sudo apt install -y ./adb-auto_1.0.0_all.deb
```

Or if installing from a local clone of this repository:

```bash
sudo apt install -y ./dist/adb-auto_1.0.0_all.deb
```

### Option 2: Portable Tarball (`.tar.gz`) — No Root Required
Installs into `~/.local/bin/adb-auto`:

```bash
tar -xzf dist/adb-auto-1.0.0.tar.gz
cd adb-auto-1.0.0
./install.sh
```

---

## First-Time Pairing (`adb-auto --pair`)

You only need to pair **once**:

1. In **Settings -> System -> Developer options -> Wireless debugging**, tap **Pair device with pairing code** to display the 6-digit PIN:
   ![Pair device with pairing code](docs/images/04-pair-with-code.png)
   ![6-digit pairing code popup](docs/images/05-pairing-code-popup.png)
2. Keep that popup open and run:
   ```bash
   adb-auto --pair
   ```
   Enter the 6-digit PIN when prompted (no IP or port needed!). `adb-auto` pairs and connects automatically.

---

## Daily Usage & Options (`adb-auto --help`)

Once paired, simply run `adb-auto` anytime Wireless Debugging is ON:

```text
usage: adb-auto [-h] [-p [PIN]] [-s] [-d] [-V]

Connect Googlebook Linux terminal to Android Wireless Debugging automatically.

options:
  -h, --help          Show this help message and exit
  -p, --pair [PIN]    Pair device using 6-digit PIN (first-time setup)
  -s, --status        Show pairing state, IP addresses, and connection status
  -d, --disconnect    Disconnect all ADB sessions
  -V, --version       Show version and license information
```

### Examples

```bash
# Connect automatically (when Wireless Debugging is ON)
adb-auto

# Pair for the first time (prompts for 6-digit PIN)
adb-auto --pair

# Pair with PIN 123456 and connect immediately
adb-auto --pair 123456

# Check pairing and connection status
adb-auto --status

# Disconnect ADB
adb-auto --disconnect
```

---

## Building From Source

Rebuild both `dist/adb-auto_1.0.0_all.deb` and `dist/adb-auto-1.0.0.tar.gz`:

```bash
./build_release.sh
```

---

## License

Distributed under the **GNU General Public License v2.0 (GPL-2.0-only)**. See [LICENSE](LICENSE) for full details.
