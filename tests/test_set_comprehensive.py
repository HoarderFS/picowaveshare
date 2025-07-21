#!/usr/bin/env python3
"""Comprehensive SET command test"""

import os
import sys
import time

import serial

# Add parent directory to path for test utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.test_utils import get_test_port


def test_set_command():
    """Test SET command comprehensively"""
    port = get_test_port()
    if not port:
        print("ERROR: No relay board found!")
        print("Connect a board or set RELAY_PORT environment variable")
        return

    print(f"Found Pico on {port}")
    print("Waiting for Pico to boot...")
    time.sleep(3)

    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(1)

        # Clear buffer
        ser.read_all()

        # Test connection
        print("\n1. Testing connection with PING:")
        ser.write(b"PING\n")
        time.sleep(0.2)
        response = ser.read_all().decode().strip()
        print(f"   Response: '{response}'")

        if "PONG" not in response:
            print("   ✗ Protocol server not responding")
            print("   The Pico may not be running main.py")
            ser.close()
            return

        print("   ✓ Protocol server is running!")

        # Test SET commands
        test_patterns = [
            ("00000000", "All relays OFF"),
            ("11111111", "All relays ON"),
            ("10101010", "Alternating pattern (8,6,4,2 ON)"),
            ("01010101", "Alternating pattern (7,5,3,1 ON)"),
            ("11110000", "First 4 relays ON (8,7,6,5)"),
            ("00001111", "Last 4 relays ON (4,3,2,1)"),
            ("10000001", "Relays 8 and 1 ON"),
            ("00011000", "Relays 4 and 5 ON"),
        ]

        print("\n2. Testing SET command patterns:")
        for pattern, description in test_patterns:
            print(f"\n   Testing: SET {pattern} - {description}")

            # Send SET command
            ser.write(f"SET {pattern}\n".encode())
            time.sleep(0.2)
            response = ser.read_all().decode().strip()
            print(f"   SET Response: '{response}'")

            # Verify with STATUS
            ser.write(b"STATUS\n")
            time.sleep(0.2)
            status = ser.read_all().decode().strip()
            print(f"   STATUS: '{status}'")

            if response == "OK" and status == pattern:
                print("   ✓ Success!")
            else:
                print("   ✗ Failed!")

            time.sleep(0.5)

        # Test invalid patterns
        print("\n3. Testing invalid SET patterns:")
        invalid_patterns = [
            ("1010101", "Too short"),
            ("101010101", "Too long"),
            ("1010X010", "Invalid character"),
            ("12345678", "Invalid digits"),
            ("", "Empty pattern"),
        ]

        for pattern, description in invalid_patterns:
            print(f"\n   Testing: SET {pattern} - {description}")
            ser.write(f"SET {pattern}\n".encode())
            time.sleep(0.2)
            response = ser.read_all().decode().strip()
            print(f"   Response: '{response}'")

            if "ERROR" in response:
                print("   ✓ Correctly rejected!")
            else:
                print("   ✗ Should have been rejected!")

        # Clean up
        print("\n4. Resetting all relays:")
        ser.write(b"ALL OFF\n")
        time.sleep(0.2)
        response = ser.read_all().decode().strip()
        print(f"   Response: '{response}'")

        ser.close()
        print("\nSET command test complete!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_set_command()
