#!/usr/bin/env python3
import sys
import time
from pathlib import Path

import serial

# Add parent directory to path for test utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import get_test_port

print("Testing connection to Pico...")

# Connect to Pico
port = get_test_port()
if not port:
    print("ERROR: No relay board found!")
    print("Connect a board or set RELAY_PORT environment variable")
    sys.exit(1)

ser = serial.Serial(port, 115200, timeout=2)
time.sleep(2)

# Send Ctrl-C to get to REPL
ser.write(b"\x03")
time.sleep(0.5)

# Clear buffer
ser.read_all()

# Send a simple command and read response
print("\nSending: 2+2")
ser.write(b"2+2\r\n")
time.sleep(0.5)

response = ser.read_all().decode("utf-8", errors="ignore")
print(f"Response: {response}")

# Try to get MicroPython version
print("\nChecking MicroPython version...")
ser.write(b"import sys\r\n")
time.sleep(0.1)
ser.write(b"sys.version\r\n")
time.sleep(0.5)

response = ser.read_all().decode("utf-8", errors="ignore")
print(f"Response: {response}")

# Test if we can read pin state
print("\nTesting pin read...")
ser.write(b"from machine import Pin\r\n")
time.sleep(0.1)
ser.write(b"p = Pin(25, Pin.OUT)\r\n")
time.sleep(0.1)
ser.write(b"p.value(1)\r\n")
time.sleep(0.1)
ser.write(b'print("LED is:", p.value())\r\n')
time.sleep(0.5)

response = ser.read_all().decode("utf-8", errors="ignore")
print(f"Response: {response}")

ser.close()
