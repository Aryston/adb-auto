# `adb-auto` — Wireless ADB Auto-Connector for Googlebook

[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Built with Google Antigravity](https://img.shields.io/badge/Vibe--Coded_with-Google_Antigravity-4285F4?logo=google)](https://deepmind.google/)

A minimalist Debian CLI tool that automatically connects the **Googlebook (Android Laptop)** Linux terminal to Android Wireless Debugging—no manual IP address or random port lookups required.

> **Credits:** Created by **[Igor Jagec (@Aryston)](https://github.com/Aryston)**, vibe-coded with **Google Antigravity** (Google DeepMind), and QA tested by **Denny Lockhart**. Licensed under **GNU GPL v2.0**.

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

Add the [`googlebook-tools`](https://salsa.debian.org/prospero/googlebook-tools) APT repository on Debian Salsa to install `/usr/bin/adb-auto`, the `man adb-auto` page, required system dependencies (`adb`, `python3`, `iproute2`, `iputils-ping`), and receive automatic `apt` updates:

```bash
echo "deb [trusted=yes] https://salsa.debian.org/prospero/googlebook-tools/-/raw/main apt/" | sudo tee /etc/apt/sources.list.d/googlebook-tools.list
sudo apt update
sudo apt install -y adb-auto
```

---

## First-Time Setup (1-Time Pairing)

Pairing is a standard Android security handshake required only **once**:

1. Go to **Settings -> System -> Developer options -> Wireless debugging**.
2. Tap **Pair device with pairing code** (a popup displays the IP, port, and a 6-digit Wi-Fi pairing code):
   ![6-digit pairing code popup](docs/images/05-pairing-code-popup.png)
3. In your Linux terminal, run the pairing command shown on the screen:
   ```bash
   adb pair 192.168.0.8:<PORT> <6-DIGIT-CODE>
   ```
4. Now run **`adb-auto`** to connect automatically!

> [!TIP]
> **1-Tap Daily Toggle (Quick Settings Tile):**
> Instead of opening Android Settings every day, add the **Wireless debugging** tile to your Quick Settings panel:
> **Settings -> System -> Developer options -> Quick Settings developer tiles -> Toggle "Wireless debugging" ON**.
>
> Now you can wake or re-enable Wireless Debugging with a single tap next to Wi-Fi!

---

## Daily Usage & Options (`adb-auto --help`)

Once paired, simply run `adb-auto` anytime Wireless Debugging is ON:

```text
usage: adb-auto [-h] [-s] [-d] [-V]

Connect Googlebook Linux terminal to Android Wireless Debugging automatically.

options:
  -h, --help        Show this help message and exit
  -s, --status      Show pairing state, IP addresses, and connection status
  -d, --disconnect  Disconnect all ADB sessions
  -V, --version     Show version and license information
```

### Examples

```bash
# Connect automatically (when Wireless Debugging is ON)
adb-auto

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
