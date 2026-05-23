# Changelog

## v1.2.0 (2026-05-23) — FT85BD Reverse Engineering

### Added
- **Bootloader protocol**: `ftesc/stm32_bootloader.py` — STM32/AT32 UART bootloader client (sync, erase, write, go)
- **`flash_firmware.py`**: Flash FT85BD firmware via bootloader protocol (cmd 60 or BOOT0 pin)
- **Firmware extraction**: Two 64KB FT85BD v1.5 binaries extracted from official tool (`ft85bd_fw.bin`, `ft85bd_fw_v2.bin`)
- **`debug_comm.py`**: Interactive serial debug tool for raw protocol exploration
- **`serial_bridge.py`**: Serial MITM bridge for Wine ←→ ESC traffic capture
- **`ftesc/motor_detection.py`**: Motor parameter auto-detection (experimental)
- **Cmd 60** (`ENTER_BOOTLOADER`) and **cmd 61** (`CHECK_MCU_HEALTH`) in protocol enum
- **Lights tab**: `gui/panels/config_tabs/lights.py` — headlight/brakelight/buzzer controls

### Changed
- **Recovery panel**: renamed "🆘 Réanimation" → "🆘 Enter Bootloader Mode" (`gui/panels/recovery.py`)
- **GUI title**: "FFTESC - Free FTESC Tool" (`gui/app.py`)
- **Cmd 2 parser**: payload is 32 bytes (not 28), 4 extra bytes after RPM

### Fixed
- **Protocol scan**: Verified 23 responding commands (0, 2, 17, 25, 26, 29, 30, 39, 60, 61...)
- **SET_SPEED (cmd 39)**: confirmed working, motor twitches at 200–1000 RPM

### Hardware Research
- **MCU identified**: Artery Technology **AT32** (not STM32F4), USB PID `2e3c:7570`
- **Bootloader**: AT32 system bootloader requires `BOOT0=1` on reset — cmd 60 does not trigger it
- **VESC protocol**: FT85BD ignores VESC protocol entirely
- **Config commands (40–43)**: No response from FT85BD (read/write not supported on this model)
- **Firmware storage**: bootloader in sectors 0–3 (64KB), app in sector 4 (64KB at `0x08010000`)

### Known Issues
- `ENTER_BOOTLOADER` (cmd 60) does nothing on FW v6.239 — may require TEA-encrypted payload
- Cannot flash v1.5 without BOOT0 hardware access or working cmd 60
- Cannot read/write EEPROM config (cmd 40/41) — no response from FT85BD
- FOC requires calibrated parameters (motor detection not yet completed)

---

## v1.01 (2026-05-21) — Initial Release

### Features
- Real-time telemetry (duty, current, RPM, temps, CPU load)
- 7 config tabs (Motor, Limits, Dual, Inputs, Battery, Comms, Advanced)
- 12 config sections with full encode/decode round-trip
- Wizard 4-step config assistant (D30 calculation)
- Simulation mode (dual motor without hardware)
- Recovery panel (MCU diagnostic, bootloader guide)
- 6 languages (FR, EN, DE, ES, PL, IT)
- Profile save/load/delete (JSON)
- CSV data logging
- Dual motor A/B/Both selector
- Validation UI with red/green borders
- 118 contextual tooltips
- Theme switching (dark/light)

### Build
- PyInstaller bundle support
- SVG→PNG logo caching
- 163+ pytest unit tests
