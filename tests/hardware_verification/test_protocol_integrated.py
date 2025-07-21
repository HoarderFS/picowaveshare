#!/usr/bin/env python3
"""
Hardware Test 3.1: Basic Protocol - Integrated Test
Upload all files to Pico and test the full protocol via serial terminal
"""

import sys
import time
from pathlib import Path

import serial

# Add parent directory to path for test utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import get_test_port


def find_pico_port():
    """Find the Pico serial port"""
    port = get_test_port()
    if not port:
        return None

    try:
        ser = serial.Serial(port, 115200, timeout=1)
        print("Found Pico at " + port)
        return ser
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None


def send_command(ser, cmd):
    """Send a command and get response"""
    print("Sending: " + cmd)
    ser.write((cmd + "\n").encode())
    time.sleep(0.5)

    response = ""
    start_time = time.time()
    while time.time() - start_time < 2:  # 2 second timeout
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            response += data
            if "\n" in response:
                break
        time.sleep(0.1)

    # Extract just the response line
    lines = response.strip().split("\n")
    for line in lines:
        if line.strip() and not line.startswith(">"):
            return line.strip()

    return response.strip()


def test_hardware_protocol():
    """Test the protocol on hardware"""
    print("=== HARDWARE TEST 3.1: BASIC PROTOCOL ===")

    # Find Pico
    ser = find_pico_port()
    if not ser:
        print("ERROR: Could not find Pico")
        return False

    # Reset Pico
    print("Resetting Pico...")
    ser.write(b"\x04")  # Ctrl-D
    time.sleep(2)
    ser.read_all()

    # Start the main program
    print("Starting protocol server...")
    ser.write(b"import main\n")
    time.sleep(1)

    # Look for "Ready" message
    start_time = time.time()
    system_ready = False
    while time.time() - start_time < 10:  # 10 second timeout
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            print(data, end="")
            if "Ready" in data:
                system_ready = True
                break
        time.sleep(0.1)

    if not system_ready:
        print("ERROR: System did not start properly")
        ser.close()
        return False

    print("\nSystem ready! Starting protocol tests...")
    print("-" * 50)

    # Test cases
    test_cases = [
        ("PING", "PONG"),
        ("STATUS", "00000000"),
        ("ON 1", "OK"),
        ("STATUS", "00000001"),
        ("ON 3", "OK"),
        ("STATUS", "00000101"),
        ("OFF 1", "OK"),
        ("STATUS", "00000100"),
        ("ALL ON", "OK"),
        ("STATUS", "11111111"),
        ("ALL OFF", "OK"),
        ("STATUS", "00000000"),
        ("ON 9", "ERROR:INVALID_RELAY_NUMBER"),
        ("INVALID", "ERROR:INVALID_COMMAND"),
    ]

    passed = 0
    failed = 0

    for cmd, expected in test_cases:
        response = send_command(ser, cmd)
        print("  Response: " + response)

        if expected in response:
            print("  ✓ PASS")
            passed += 1
        else:
            print("  ✗ FAIL (expected: " + expected + ")")
            failed += 1
        print()

    # Stop the server
    print("Stopping server...")
    send_command(ser, "EXIT")

    ser.close()

    print("=" * 50)
    print("TEST RESULTS:")
    print("  Passed: " + str(passed))
    print("  Failed: " + str(failed))
    print("  Total:  " + str(passed + failed))

    return failed == 0


if __name__ == "__main__":
    success = test_hardware_protocol()
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("Hardware Test 3.1 Complete")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Hardware Test 3.1 Failed")
