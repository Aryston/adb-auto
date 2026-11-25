# Changelog

All notable changes to `adb-auto` are documented in this file.
Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.3.0] - 2026-11-25

### Added
- Quick Settings tile guidance and walk-through screenshots for 1-tap recovery after laptop sleep.
- Bit-for-bit reproducible builds enforced with `SOURCE_DATE_EPOCH` and timestamp clamping.
- Native Debian changelog integration (`apt-get changelog adb-auto`).

### Changed
- Removed obsolete `--pair` / `-p` flags in favor of native `adb pair`.
- Dropped legacy `.tar.gz` archive generation to focus solely on native Debian packaging.
- Passed full Debian Lintian policy compliance (`lintian -EvIL +pedantic` with 0 errors, 0 warnings).

## [1.1.0] - 2026-11-16

### Added
- Automatic detection of unconfigured pairing state with actionable recovery guidance.
- Improved warning instructions when Wireless Debugging is disabled or suspended.

### Changed
- Removed fragile socket port-scan relay from initial pairing logic.

## [1.0.0] - 2026-11-08

### Added
- Initial release for Googlebook (Android Laptop).
- Automated TTL=1 host discovery and asynchronous ADB socket scanner.
