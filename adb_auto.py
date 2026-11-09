#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
#
# adb-auto — Minimalist Wireless ADB Auto-Connector for Googlebook (Android Laptop)
#
# Vibe-coded with Google Antigravity (Google DeepMind Agentic Coding Assistant).
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

"""
adb-auto: Minimalist Wireless ADB Auto-Connector for Googlebook (Android Laptop).

Connects the Googlebook Linux terminal to Android Wireless Debugging automatically.
Built with Google Antigravity. Licensed under GNU GPL v2.0.
"""

import argparse
import asyncio
import re
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

VERSION = "1.0.0"
CACHE_DIR = Path.home() / ".cache" / "adb-auto"
LAST_IP_FILE = CACHE_DIR / "last_wifi_ip"
KNOWN_HOSTS_FILE = Path.home() / ".android" / "adb_known_hosts.pb"


def _build_adb_cnxn() -> bytes:
    """Build standard 24-byte ADB CNXN header + 'host::\\0' payload."""
    payload = b"host::\x00"
    cmd = 0x4E584E43  # "CNXN"
    arg0 = 0x01000001
    arg1 = 1048576
    crc = sum(payload) & 0xFFFFFFFF
    magic = cmd ^ 0xFFFFFFFF
    return struct.pack("<IIIIII", cmd, arg0, arg1, len(payload), crc, magic) + payload


ADB_CNXN_PACKET = _build_adb_cnxn()
ADB_VALID_HEADERS = (b"STLS", b"CNXN", b"AUTH")


def run_cmd(args: List[str], timeout: float = 5.0) -> Tuple[int, str, str]:
    try:
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def is_paired() -> Tuple[bool, Optional[str]]:
    """Check if ~/.android/adb_known_hosts.pb exists and has a paired host identifier."""
    if not KNOWN_HOSTS_FILE.exists():
        return False, None
    try:
        raw = KNOWN_HOSTS_FILE.read_bytes()
        if len(raw) < 4:
            return False, None
        m = re.search(rb"(adb-[A-Za-z0-9_-]+)", raw)
        host_id = m.group(1).decode("ascii", errors="ignore") if m else "paired-host"
        return True, host_id
    except Exception:
        return True, "paired-host"


def get_live_devices() -> List[str]:
    """
    Return list of genuinely responsive ADB device serials.
    Verifies each 'device' entry with `adb -s <serial> shell true`,
    automatically disconnecting dead or offline sockets.
    """
    rc, out, _ = run_cmd(["adb", "devices"], timeout=5.0)
    if rc != 0:
        return []
    live = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        if state == "device":
            ping_rc, _, _ = run_cmd(["adb", "-s", serial, "shell", "true"], timeout=1.5)
            if ping_rc == 0:
                live.append(serial)
            else:
                run_cmd(["adb", "disconnect", serial], timeout=2.0)
        elif state in ("offline", "unauthorized"):
            run_cmd(["adb", "disconnect", serial], timeout=2.0)
    return live


def get_vm_gateway_ip() -> Optional[str]:
    """Return the Linux VM's default gateway IP (the local Android Host virtual bridge)."""
    rc, out, _ = run_cmd(["ip", "route", "show", "default"], timeout=2.0)
    if rc == 0:
        m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", out)
        if m:
            return m.group(1)
    rc, out, _ = run_cmd(["ping", "-t", "1", "-c", "1", "-W", "1", "8.8.8.8"], timeout=2.0)
    m = re.search(r"From (\d+\.\d+\.\d+\.\d+)", out)
    return m.group(1) if m else None


def is_local_host_ip(ip: str) -> bool:
    """
    Verify if `ip` belongs to the local Android Host itself using a TTL=1 ping.
    Only the local Android Host is 1 hop away from the Linux VM (ttl=64, rc=0);
    all other LAN devices are 2 hops away ('Time to live exceeded', rc=1).
    """
    rc, out, _ = run_cmd(["ping", "-t", "1", "-c", "1", "-W", "1", ip], timeout=1.5)
    return rc == 0 and "bytes from" in out


async def discover_host_wifi_ip(gw_ip: Optional[str]) -> Optional[str]:
    """Automatically discover the Android Host's active Wi-Fi/LAN IP address."""
    if LAST_IP_FILE.exists():
        try:
            cached_ip = LAST_IP_FILE.read_text().strip()
            if cached_ip and cached_ip != gw_ip and is_local_host_ip(cached_ip):
                return cached_ip
        except Exception:
            pass

    subnets = []
    for target in ("8.8.8.8", "1.1.1.1"):
        _, out, _ = run_cmd(["ping", "-t", "2", "-c", "1", "-W", "1", target], timeout=2.0)
        m = re.search(r"From (\d+\.\d+\.\d+)\.\d+", out)
        if m:
            subnets.append(m.group(1))
            break

    for fb in ("192.168.0", "192.168.1", "10.0.0", "172.20.10"):
        if fb not in subnets:
            subnets.append(fb)

    sem = asyncio.Semaphore(64)

    async def check_ip(ip: str) -> Optional[str]:
        async with sem:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-t", "1", "-c", "1", "-W", "1", ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and b"bytes from" in stdout:
                return ip
            return None

    for prefix in subnets:
        tasks = [check_ip(f"{prefix}.{i}") for i in range(1, 255)]
        results = await asyncio.gather(*tasks)
        found = [ip for ip in results if ip is not None]
        if found:
            host_ip = found[0]
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                LAST_IP_FILE.write_text(host_ip)
            except Exception:
                pass
            return host_ip

    return None


async def probe_adb_port(
    ip: str, port: int, sem: asyncio.Semaphore, send_cnxn: bool = True
) -> Optional[Tuple[int, bool]]:
    """
    Check if `ip:port` is open and whether it responds with an ADB protocol header
    (STLS, CNXN, or AUTH). Returns (port, is_confirmed_adb) or None if closed.
    """
    async with sem:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=0.15
            )
            is_adb = False
            if send_cnxn:
                try:
                    writer.write(ADB_CNXN_PACKET)
                    await writer.drain()
                    resp = await asyncio.wait_for(reader.read(24), timeout=0.6)
                    if len(resp) >= 4 and resp[:4] in ADB_VALID_HEADERS:
                        is_adb = True
                except Exception:
                    pass
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return (port, is_adb)
        except Exception:
            return None


async def scan_for_adb_ports(
    wifi_ip: str,
    gw_ip: Optional[str],
    port_range: Tuple[int, int] = (30000, 61000),
    send_cnxn: bool = True,
) -> Tuple[List[int], List[int]]:
    """
    Scan `wifi_ip` for open ports in `port_range`.
    Excludes ports that are also open on `gw_ip` (internal VM services bound to 0.0.0.0)
    unless they explicitly respond with an ADB header.
    """
    sem = asyncio.Semaphore(512)
    start_p, end_p = port_range

    tasks = [probe_adb_port(wifi_ip, p, sem, send_cnxn=send_cnxn) for p in range(start_p, end_p)]
    results = await asyncio.gather(*tasks)
    open_items = [r for r in results if r is not None]

    confirmed = [p for p, is_adb in open_items if is_adb]
    unconfirmed = [p for p, is_adb in open_items if not is_adb and 30000 <= p < 50000]

    candidates = []
    if gw_ip and unconfirmed:
        gw_checks = await asyncio.gather(
            *(probe_adb_port(gw_ip, p, sem, send_cnxn=False) for p in unconfirmed)
        )
        gw_open = {r[0] for r in gw_checks if r is not None}
        candidates = [p for p in unconfirmed if p not in gw_open]
    else:
        candidates = unconfirmed

    return confirmed, candidates


def try_adb_connect(ip: str, port: int, timeout: float = 4.0) -> bool:
    """Attempt `adb connect ip:port`, verify responsiveness, and disable 7-day key expiry."""
    target = f"{ip}:{port}"
    rc, out, _ = run_cmd(["adb", "connect", target], timeout=timeout)
    if "connected to" in out or "already connected" in out:
        time.sleep(0.3)
        live = get_live_devices()
        if target in live or any(d.startswith(ip) for d in live):
            run_cmd(
                ["adb", "-s", target, "shell", "settings", "put", "global", "adb_allowed_connection_time", "0"],
                timeout=2.0,
            )
            return True
    run_cmd(["adb", "disconnect", target], timeout=2.0)
    return False


def print_wireless_off_warning(wifi_ip: Optional[str], paired: bool) -> None:
    if not paired:
        print(
            "\n[✗] Device is not paired with Linux ADB yet.\n"
            "    1. Open Settings -> System -> Developer options -> Wireless debugging\n"
            "    2. Tap 'Pair device with pairing code'\n"
            "    3. Run: adb-auto --pair <6-digit-PIN>",
            file=sys.stderr,
        )
        return

    ip_label = wifi_ip or "Googlebook"
    print(
        f"\n[✗] Wireless Debugging is OFF or suspended on {ip_label}.\n"
        "    Note: Android requires 'Use wireless debugging' to be turned ON manually\n"
        "    (Settings -> System -> Developer options -> Wireless debugging).\n"
        "    If the switch is already ON but says 'Unavailable', toggle it OFF and ON.",
        file=sys.stderr,
    )


async def pair_with_pin(wifi_ip: str, gw_ip: Optional[str], pin_code: Optional[str]) -> bool:
    """
    Discover the open SPAKE2+ pairing port on `wifi_ip` and run `adb pair ip:port pin`.
    The user only provides the 6-digit PIN code.
    """
    if not pin_code:
        print(
            "First-Time Wireless ADB Pairing:\n"
            "  1. Open Settings -> System -> Developer options -> Wireless debugging\n"
            "  2. Tap 'Pair device with pairing code' (keep the popup open on screen)"
        )
        try:
            pin_code = input("Enter 6-digit pairing code: ").strip()
        except EOFError:
            return False

    pin_code = re.sub(r"\s+", "", pin_code or "")
    if not re.match(r"^\d{6}$", pin_code):
        print(f"[✗] Invalid pairing code '{pin_code}'. Expected a 6-digit number.", file=sys.stderr)
        return False

    print(f"[*] Scanning {wifi_ip} for active pairing port...")
    _, candidates = await scan_for_adb_ports(wifi_ip, gw_ip, send_cnxn=False)
    if not candidates:
        print_wireless_off_warning(wifi_ip, paired=True)
        return False

    for port in candidates:
        target = f"{wifi_ip}:{port}"
        print(f"[*] Trying adb pair {target} ...")
        rc, out, err = run_cmd(["adb", "pair", target, pin_code], timeout=6.0)
        combined = f"{out} {err}"
        if "Successfully paired" in combined:
            print(f"[✓] {out or 'Successfully paired!'}")
            return True

    print(
        f"\n[✗] Pairing failed on discovered port(s): {candidates}.\n"
        "    Verify that the 6-digit code matches the popup currently shown on screen.",
        file=sys.stderr,
    )
    return False


async def print_status() -> int:
    paired, host_id = is_paired()
    gw_ip = get_vm_gateway_ip()
    wifi_ip = await discover_host_wifi_ip(gw_ip)
    devices = get_live_devices()

    print("=== adb-auto Status ===")
    print(f"Version          : {VERSION}")
    print(f"Pairing Status   : {'Paired (' + (host_id or 'ok') + ')' if paired else 'Not paired (run `adb-auto --pair`)'}")
    print(f"VM Gateway IP    : {gw_ip or 'Not detected'}")
    print(f"Googlebook IP    : {wifi_ip or 'Not detected'}")
    if devices:
        print(f"ADB Connection   : Connected ({', '.join(devices)})")
        _, model, _ = run_cmd(["adb", "-s", devices[0], "shell", "getprop", "ro.product.model"], timeout=2.0)
        _, rel, _ = run_cmd(["adb", "-s", devices[0], "shell", "getprop", "ro.build.version.release"], timeout=2.0)
        if model or rel:
            print(f"Device Info      : {model or 'Unknown'} (Android {rel or '?'})")
        return 0
    else:
        print("ADB Connection   : Disconnected")
        print_wireless_off_warning(wifi_ip, paired)
        return 1


async def async_main(args: argparse.Namespace) -> int:
    if args.disconnect:
        rc, out, _ = run_cmd(["adb", "disconnect"], timeout=4.0)
        print(f"[✓] {out or 'Disconnected all ADB sessions.'}")
        return rc

    if args.status:
        return await print_status()

    if args.pair is None:
        existing = get_live_devices()
        if existing:
            print(f"[✓] Already connected to ADB: {', '.join(existing)}")
            return 0

    gw_ip = get_vm_gateway_ip()
    t0 = time.time()
    wifi_ip = await discover_host_wifi_ip(gw_ip)
    if not wifi_ip:
        print(
            "[✗] Could not detect Googlebook Wi-Fi IP. Ensure Wi-Fi is connected.",
            file=sys.stderr,
        )
        return 1

    print(f"[*] Googlebook local IP detected: {wifi_ip} (gateway: {gw_ip or 'unknown'}) [{time.time() - t0:.2f}s]")

    paired, _ = is_paired()
    if args.pair is not None or not paired:
        pin = args.pair if isinstance(args.pair, str) and args.pair != "" else None
        if not paired and args.pair is None:
            print("[!] Device is not paired yet. Starting first-time pairing...")
        ok = await pair_with_pin(wifi_ip, gw_ip, pin)
        if not ok:
            return 1
        await asyncio.sleep(0.8)

    t_scan = time.time()
    print(f"[*] Scanning {wifi_ip} for active Wireless Debugging port...")
    confirmed, candidates = await scan_for_adb_ports(wifi_ip, gw_ip)
    scan_dt = time.time() - t_scan

    ports_to_try = confirmed + [p for p in candidates if p not in confirmed]
    if ports_to_try:
        print(f"[*] Found candidate port(s) {ports_to_try} in {scan_dt:.2f}s. Connecting...")
        for port in ports_to_try:
            if try_adb_connect(wifi_ip, port):
                print(f"[✓] Connected to Wireless Debugging at {wifi_ip}:{port}!")
                return 0

    print_wireless_off_warning(wifi_ip, paired=True)
    return 1


def build_parser() -> argparse.ArgumentParser:
    epilog = """examples:
  adb-auto                Connect automatically (when Wireless Debugging is ON)
  adb-auto --pair         Pair for the first time (prompts for 6-digit PIN)
  adb-auto --pair 123456  Pair with PIN 123456 and connect immediately
  adb-auto --status       Check pairing and connection status
  adb-auto --disconnect   Disconnect ADB

note:
  Requires 'Use wireless debugging' to be turned ON in Android Settings:
  Settings -> System -> Developer options -> Wireless debugging

  Android automatically suspends Wireless Debugging after sleep or Wi-Fi
  changes (sometimes showing 'Unavailable' while the switch still looks ON).
  If connection fails, toggle 'Use wireless debugging' OFF and back ON.

Built with Google Antigravity | License: GNU GPL v2.0 (GPL-2.0-only)
"""
    parser = argparse.ArgumentParser(
        prog="adb-auto",
        description="Connect Googlebook Linux terminal to Android Wireless Debugging automatically.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-p",
        "--pair",
        nargs="?",
        const="",
        metavar="PIN",
        help="Pair device using 6-digit PIN (first-time setup)",
    )
    parser.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Show pairing state, IP addresses, and connection status",
    )
    parser.add_argument(
        "-d",
        "--disconnect",
        action="store_true",
        help="Disconnect all ADB sessions",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION} (Built with Google Antigravity, License: GPL-2.0)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\n[!] Cancelled by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
