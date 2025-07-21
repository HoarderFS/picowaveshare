#!/usr/bin/env python3
"""Test SET command on hardware"""

import sys
import time
from pathlib import Path

import serial

# Add parent directory to path for test utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.test_utils import get_test_port

PORT = get_test_port()
BAUDRATE = 115200


def test_set_command():
    """Test the SET command"""
    if not PORT:
        print("ERROR: No relay board found!")
        print("Connect a board or set RELAY_PORT environment variable")
        return 1

    print(f"Testing SET command on hardware at {PORT}...")

    # Wait for Pico to boot
    time.sleep(3)

    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        time.sleep(1)

        # Clear buffer
        ser.read_all()

        # Test 1: Basic SET command
        print("\n1. Testing SET 11110000:")
        ser.write(b"SET 11110000\n")
        time.sleep(0.1)
        response = ser.read_all().decode().strip()
        print(f"   Response: {response}")

        # Verify with STATUS
        ser.write(b"STATUS\n")
        time.sleep(0.1)
        status = ser.read_all().decode().strip()
        print(f"   Status: {status}")
        print(
            "   ✓ Success!"
            if status == "11110000"
            else "   ✗ Failed - expected 11110000"
        )

        # Test 2: Different pattern
        print("\n2. Testing SET 01010101:")
        ser.write(b"SET 01010101\n")
        time.sleep(0.1)
        response = ser.read_all().decode().strip()
        print(f"   Response: {response}")

        ser.write(b"STATUS\n")
        time.sleep(0.1)
        status = ser.read_all().decode().strip()
        print(f"   Status: {status}")
        print(
            "   ✓ Success!"
            if status == "01010101"
            else "   ✗ Failed - expected 01010101"
        )

        # Test 3: Invalid pattern
        print("\n3. Testing invalid SET 12345678:")
        ser.write(b"SET 12345678\n")
        time.sleep(0.1)
        response = ser.read_all().decode().strip()
        print(f"   Response: {response}")
        print(
            "   ✓ Success!"
            if "ERROR" in response
            else "   ✗ Failed - should return ERROR"
        )

        # Clean up
        print("\n4. Resetting all relays:")
        ser.write(b"ALL OFF\n")
        time.sleep(0.1)
        response = ser.read_all().decode().strip()
        print(f"   Response: {response}")

        ser.close()
        print("\nSET command test complete!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_set_command()
