#!/usr/bin/env python3
"""Diagnostic UART : envoie une commande et affiche TOUT ce qui revient."""
import serial, time, sys

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyS4"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1.0)
print(f"Connecté à {PORT} @ {BAUD}")
time.sleep(0.2)
ser.reset_input_buffer()

# 1) Écouter passivement 2s (l'ESC envoie peut-être des trames en continu)
print("\n--- Écoute passive 2s ---")
start = time.monotonic()
while time.monotonic() - start < 2.0:
    b = ser.read(256)
    if b:
        print(f"  Reçu {len(b)} octets: {b.hex()}")
print("  Fin écoute passive")

# 2) Envoyer OBTAIN_DATA_ONCE (commande 0)
print("\n--- Envoi OBTAIN_DATA_ONCE ---")
obtain_frame = bytes.fromhex("aa010040bfdd")  # cmd=0
print(f"  Envoi: {obtain_frame.hex()}")
ser.write(obtain_frame)
time.sleep(0.5)
resp = ser.read(256)
print(f"  Réponse ({len(resp)} octets): {resp.hex() if resp else 'RIEN'}")

# 3) Envoyer OBTAIN_FIRMWARE_VERSION (commande 17)
print("\n--- Envoi OBTAIN_FIRMWARE_VERSION ---")
fw_frame = bytes.fromhex("aa01114c7fdd")  # cmd=17
print(f"  Envoi: {fw_frame.hex()}")
ser.write(fw_frame)
time.sleep(0.5)
resp = ser.read(256)
print(f"  Réponse ({len(resp)} octets): {resp.hex() if resp else 'RIEN'}")

# 4) Envoyer OBTAIN_ALL_FTESC_ID (commande 30 = 0x1E)
print("\n--- Envoi OBTAIN_ALL_FTESC_ID ---")
id_frame = bytes.fromhex("aa011e483fdd")  # cmd=30(0x1E)
print(f"  Envoi: {id_frame.hex()}")
ser.write(id_frame)
time.sleep(0.5)
resp = ser.read(256)
print(f"  Réponse ({len(resp)} octets): {resp.hex() if resp else 'RIEN'}")

# 5) Écouter encore 1s (si l'ESC répond en différé)
print("\n--- Écoute résiduelle 1s ---")
start = time.monotonic()
while time.monotonic() - start < 1.0:
    b = ser.read(256)
    if b:
        print(f"  Reçu: {b.hex()}")
print("  Fin")

ser.close()
print("\nDiagnostic terminé.")
