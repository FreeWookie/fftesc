#!/usr/bin/env python3
"""
Serial MITM: bridges Flipsky Tool (Wine) <-> real ESC.
Captures ALL traffic.
"""

import os, sys, time, threading, struct, fcntl, termios

try:
    import serial
except ImportError:
    print("pip install pyserial")
    sys.exit(1)

ESC_PORT = "/dev/ttyACM0"
WINE_PORT_LINK = "/tmp/ttyV1"
LOG_FILE = "bridge_capture.bin"

# Remove old symlink
if os.path.exists(WINE_PORT_LINK):
    os.unlink(WINE_PORT_LINK)

# Create PTY: Wine opens the slave, we read from master
master_fd, slave_fd = os.openpty()
slave_name = os.ttyname(slave_fd)
os.symlink(slave_name, WINE_PORT_LINK)
print(f"[+] Wine serial port: {WINE_PORT_LINK} -> {slave_name}")

# Configure master for raw binary
for fd in [master_fd, slave_fd]:
    attrs = termios.tcgetattr(fd)
    for flag_attr in [0, 1, 2, 3]:
        # Get current flags
        pass
    # Set raw mode
    attrs[0] = attrs[0] & ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                            termios.ISTRIP | termios.INLCR | termios.IGNCR |
                            termios.ICRNL | termios.IXON | termios.IXOFF)
    attrs[1] = attrs[1] & ~termios.OPOST
    attrs[2] = attrs[2] & ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    attrs[2] = attrs[2] | termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3] = attrs[3] & ~(termios.ECHO | termios.ECHONL | termios.ICANON |
                            termios.ISIG | termios.IEXTEN)
    attrs[6][termios.VMIN] = 1
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)

log = open(LOG_FILE, "ab")
print(f"[+] Logging to {LOG_FILE}")
running = True

def forward_esc_to_wine(ser, master_fd):
    """ESC -> Wine"""
    while running:
        try:
            data = ser.read(4096)
            if not data:
                continue
            log.write(struct.pack('>d', time.time()))
            log.write(b'<<<')
            log.write(data)
            log.flush()
            print(f"[ESC->WINE] ({len(data)}B): {data[:64].hex()}")
            os.write(master_fd, data)
        except serial.SerialException:
            break
        except OSError:
            break

def forward_wine_to_esc(ser, master_fd):
    """Wine -> ESC"""
    while running:
        try:
            data = os.read(master_fd, 4096)
            if not data:
                break
            log.write(struct.pack('>d', time.time()))
            log.write(b'>>>')
            log.write(data)
            log.flush()
            print(f"[WINE->ESC] ({len(data)}B): {data[:64].hex()}")
            ser.write(data)
        except OSError:
            break

print("[+] Starting bridge...")
print(f"[+] Configure Wine: wine reg add \"HKEY_LOCAL_MACHINE\\\\Software\\\\Wine\\\\Ports\" /v COM1 /t REG_SZ /d {WINE_PORT_LINK}")
print()

# Wait for ESC
while not os.path.exists(ESC_PORT):
    print(f"[-] Waiting for {ESC_PORT} (ESC not connected)...")
    time.sleep(2)

print(f"[+] Opening {ESC_PORT}...")
ser = serial.Serial(ESC_PORT, 115200, timeout=0.1)

t1 = threading.Thread(target=forward_esc_to_wine, args=(ser, master_fd), daemon=True)
t2 = threading.Thread(target=forward_wine_to_esc, args=(ser, master_fd), daemon=True)
t1.start()
t2.start()

try:
    while running:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[+] Stopping...")
finally:
    running = False
    ser.close()
    log.close()
    os.close(master_fd)
    os.close(slave_fd)
    if os.path.exists(WINE_PORT_LINK):
        os.unlink(WINE_PORT_LINK)
    print("[+] Done")