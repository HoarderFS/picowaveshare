"""
Simple Hardware Protocol Test
Tests the ASCII protocol with main.py already running
"""

import time

import serial
import serial.tools.list_ports
from waveshare_relay.discovery import find_relay_board


def test_protocol_direct():
    """Test protocol commands via direct serial communication"""
    print("=== HARDWARE TEST: PROTOCOL VERIFICATION ===")

    # Find board
    port = find_relay_board()
    if not port:
        print("ERROR: No relay board found")
        return False

    print(f"Found board at {port}")

    # Open serial connection
    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(0.5)  # Let port settle

    # Clear buffers
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Test commands
    test_commands = [
        ("PING", "PONG"),
        ("STATUS", "00000000"),
        ("ON 1", "OK"),
        ("STATUS", "00000001"),
        ("ON 3", "OK"),
        ("STATUS", "00000101"),
        ("OFF 1", "OK"),
        ("STATUS", "00000100"),
        ("OFF 3", "OK"),
        ("STATUS", "00000000"),
        ("ON 9", "ERROR:INVALID_RELAY_NUMBER"),
        ("INVALID", "ERROR:INVALID_COMMAND"),
        ("INFO", "WAVESHARE-PICO-RELAY-B"),  # Check INFO contains board name
        ("UID", ""),  # Just check we get a response
        ("BEEP", "OK"),
        ("BUZZ ON", "OK"),
        ("BUZZ OFF", "OK"),
    ]

    print("\nTesting protocol commands:")
    print("-" * 40)

    passed = 0
    failed = 0

    for cmd, expected in test_commands:
        print(f"\nTesting: {cmd}")

        # Clear input buffer
        ser.reset_input_buffer()

        # Send command
        ser.write((cmd + "\n").encode())
        ser.flush()

        # Wait for response
        time.sleep(0.2)
        response = ser.readline().decode().strip()
        print(f"Response: {response}")

        # Small delay between commands to prevent crashes
        time.sleep(0.1)

        # Check response
        if expected == "" and response:
            # Just checking we got a response
            print("✓ PASS")
            passed += 1
        elif expected in response:
            print("✓ PASS")
            passed += 1
        else:
            print(f"✗ FAIL - Expected: {expected}")
            failed += 1

    ser.close()

    print("\n" + "=" * 40)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 40)

    return failed == 0


if __name__ == "__main__":
    success = test_protocol_direct()
    exit(0 if success else 1)
