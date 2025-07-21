#!/usr/bin/env python3
import sys
import time
from pathlib import Path

import serial
import serial.tools.list_ports

# Add parent directory to path for test utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import get_test_port

print("Available serial ports:")
for port in serial.tools.list_ports.comports():
    print(f"  {port.device} - {port.description}")

print("\nTrying to connect to relay board...")
port = get_test_port()
if not port:
    print("ERROR: No relay board found!")
    print("Connect a board or set RELAY_PORT environment variable")
    sys.exit(1)

try:
    ser = serial.Serial(port, 115200, timeout=1)
    print(f"Connected to {port}")

    # Try different methods to get response
    print("\n1. Sending Ctrl-C (interrupt)...")
    ser.write(b"\x03")
    time.sleep(1)
    data = ser.read(1000)
    print(f"   Got {len(data)} bytes: {data[:50]}...")

    print("\n2. Sending Ctrl-D (soft reset)...")
    ser.write(b"\x04")
    time.sleep(2)
    data = ser.read(1000)
    print(f"   Got {len(data)} bytes: {data[:50]}...")

    print("\n3. Trying raw REPL (Ctrl-A)...")
    ser.write(b"\x01")
    time.sleep(0.5)
    data = ser.read(100)
    print(f"   Got {len(data)} bytes: {data}")

    ser.close()

except Exception as e:
    print(f"Error: {e}")
