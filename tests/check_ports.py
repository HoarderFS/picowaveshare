#!/usr/bin/env python3
"""Check serial ports for Pico details"""

import serial.tools.list_ports

print("Detailed port information:\n")

for port in serial.tools.list_ports.comports():
    print(f"Port: {port.device}")
    print(f"  Description: {port.description}")
    print(f"  Manufacturer: {port.manufacturer}")
    print(f"  Product: {port.product}")
    print(
        f"  VID:PID: {port.vid:04X}:{port.pid:04X}" if port.vid else "  VID:PID: None"
    )
    print(f"  Serial Number: {port.serial_number}")
    print(f"  HWID: {port.hwid}")
    print()

# Raspberry Pi Pico typically has VID:PID = 2E8A:0005
print("\nLooking for Raspberry Pi Pico (VID=2E8A)...")
pico_found = False
for port in serial.tools.list_ports.comports():
    if port.vid == 0x2E8A:  # Raspberry Pi vendor ID
        print(f"✓ Found Pico at {port.device}")
        pico_found = True

if not pico_found:
    print("✗ No Raspberry Pi Pico found")
    print("\nNote: Pico should have VID=2E8A:0005 when running MicroPython")
