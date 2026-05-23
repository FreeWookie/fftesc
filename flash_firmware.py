#!/usr/bin/env python3
"""
flash_firmware.py — Flash FT85BD firmware v1.5 to ESC

Usage:
    python3 flash_firmware.py [--port /dev/ttyUSB0] [--firmware path_to_fw.bin]

Steps:
1. Connect to ESC in normal mode (115200 8N1)
2. Send ENTER_BOOTLOADER (cmd 60) to jump to STM32 ROM bootloader
3. Reconnect with 115200 8E1 (STM32 bootloader protocol)
4. Sync, erase, write firmware to 0x08010000, verify
5. Power cycle to boot new firmware
"""

import sys, os, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ftesc.protocol import build_frame, UartCommand
from ftesc.stm32_bootloader import Stm32Bootloader


def enter_bootloader(port: str, baud: int = 115200):
    """Send ENTER_BOOTLOADER command to switch ESC to bootloader mode."""
    import serial
    print(f"[1] Connecting to {port} at {baud} 8N1...")
    ser = serial.Serial(port, baud, timeout=2)
    time.sleep(0.5)

    frame = build_frame(UartCommand.ENTER_BOOTLOADER, b'')
    print(f"    Sending ENTER_BOOTLOADER: {frame.hex()}")
    ser.write(frame)
    ser.close()
    print("    Waiting 2.5s for bootloader to initialize...")
    time.sleep(2.5)


def flash_firmware(port: str, firmware_path: str, baud: int = 115200):
    """Flash firmware via STM32 bootloader protocol."""
    print(f"[2] Connecting to STM32 bootloader at {port} {baud} 8E1...")
    bl = Stm32Bootloader(port, baud, timeout=2.0)
    bl.connect()

    print("    Syncing...")
    try:
        bl.sync()
        print("    ✅ Sync OK")
    except Exception as e:
        print(f"    ❌ Sync failed: {e}")
        bl.disconnect()
        return False

    try:
        ver, cmds = bl.get_version()
        print(f"    Bootloader v{ver}, supports {len(cmds)} commands")
        pid = bl.get_id()
        pid_val = int.from_bytes(pid, 'big') if len(pid) <= 2 else int.from_bytes(pid, 'big')
        print(f"    Chip ID: 0x{pid_val:04X}")

        print(f"\n[3] Flashing {firmware_path}...")
        bl.flash_firmware_bin(firmware_path)
        print("    ✅ Firmware flashed successfully!")

        print("\n[4] Jumping to application...")
        bl.go(0x08010000)
        print("    Jump command sent. Power cycle to boot new firmware.")
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        bl.disconnect()
        return False

    bl.disconnect()
    return True


def main():
    parser = argparse.ArgumentParser(description='Flash firmware to FT85BD ESC')
    parser.add_argument('--port', default='/dev/ttyACM0',
                        help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--firmware', default='ft85bd_fw.bin',
                        help='Firmware .bin file (default: ft85bd_fw.bin)')
    parser.add_argument('--baud', type=int, default=115200,
                        help='Baud rate (default: 115200)')
    parser.add_argument('--skip-enter', action='store_true',
                        help='Skip ENTER_BOOTLOADER (ESC already in bootloader)')
    args = parser.parse_args()

    if not os.path.exists(args.firmware):
        print(f"Error: firmware file not found: {args.firmware}")
        print("Available firmware files:")
        for f in ['ft85bd_fw.bin', 'ft85bd_fw_v2.bin']:
            if os.path.exists(f):
                print(f"  {f} ({os.path.getsize(f)} bytes)")
        return 1

    if not args.skip_enter:
        enter_bootloader(args.port, args.baud)

    success = flash_firmware(args.port, args.firmware, args.baud)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
