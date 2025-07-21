"""
Crash Investigation Test
Systematically test different scenarios to identify what causes board crashes
"""

import time

import serial
from waveshare_relay.discovery import find_relay_board


def test_rapid_commands():
    """Test sending commands rapidly without delays"""
    print("=== TEST 1: Rapid Commands ===")
    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    try:
        # Send 10 PING commands rapidly
        print("Sending 10 PINGs rapidly...")
        for _i in range(10):
            ser.write(b"PING\n")
            ser.flush()
            # No delay between commands

        # Wait and check if board is still responsive
        time.sleep(2)
        ser.reset_input_buffer()
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(0.5)
        response = ser.readline()

        if response:
            print(f"Board still responsive: {response.decode().strip()}")
            return True
        else:
            print("Board not responding - may have crashed")
            return False
    finally:
        ser.close()


def test_large_buffer():
    """Test sending a very long command"""
    print("\n=== TEST 2: Large Buffer ===")
    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    try:
        # Send a very long invalid command
        print("Sending 300 character command...")
        long_cmd = "X" * 300 + "\n"
        ser.write(long_cmd.encode())
        ser.flush()

        # Wait and check response
        time.sleep(1)
        response = ser.readline()
        print(f"Response: {response.decode().strip() if response else 'No response'}")

        # Test if still alive
        time.sleep(1)
        ser.reset_input_buffer()
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(0.5)
        response = ser.readline()

        if response:
            print(f"Board still responsive: {response.decode().strip()}")
            return True
        else:
            print("Board not responding - may have crashed")
            return False
    finally:
        ser.close()


def test_incomplete_commands():
    """Test sending commands without newlines"""
    print("\n=== TEST 3: Incomplete Commands ===")
    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    try:
        # Send commands without newlines
        print("Sending commands without newlines...")
        ser.write(b"PING")
        ser.flush()
        time.sleep(0.5)
        ser.write(b"STATUS")
        ser.flush()
        time.sleep(0.5)
        ser.write(b"INFO")
        ser.flush()

        # Now send a newline
        time.sleep(0.5)
        ser.write(b"\n")
        ser.flush()

        # Check response
        time.sleep(0.5)
        response = ser.readline()
        print(
            f"Response to concatenated command: {response.decode().strip() if response else 'No response'}"
        )

        # Test if still alive
        ser.reset_input_buffer()
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(0.5)
        response = ser.readline()

        if response:
            print(f"Board still responsive: {response.decode().strip()}")
            return True
        else:
            print("Board not responding - may have crashed")
            return False
    finally:
        ser.close()


def test_binary_data():
    """Test sending binary/non-ASCII data"""
    print("\n=== TEST 4: Binary Data ===")
    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    try:
        # Send some binary data
        print("Sending binary data...")
        ser.write(bytes([0x00, 0x01, 0xFF, 0x80, 0x0A]))  # Including newline
        ser.flush()

        # Wait for any response
        time.sleep(0.5)
        if ser.in_waiting:
            response = ser.read(ser.in_waiting)
            print(f"Response to binary: {repr(response)}")

        # Test if still alive
        time.sleep(1)
        ser.reset_input_buffer()
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(0.5)
        response = ser.readline()

        if response:
            print(f"Board still responsive: {response.decode().strip()}")
            return True
        else:
            print("Board not responding - may have crashed")
            return False
    finally:
        ser.close()


def test_mixed_line_endings():
    """Test different line ending combinations"""
    print("\n=== TEST 5: Mixed Line Endings ===")
    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    try:
        # Test different line endings
        endings = [b"\r", b"\n", b"\r\n", b"\n\r"]
        for ending in endings:
            print(f"Testing with {repr(ending)}")
            ser.reset_input_buffer()
            ser.write(b"PING" + ending)
            ser.flush()
            time.sleep(0.2)

            if ser.in_waiting:
                response = ser.readline()
                print(f"  Response: {response.decode().strip()}")

        # Test if still alive
        ser.reset_input_buffer()
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(0.5)
        response = ser.readline()

        if response:
            print(f"Board still responsive: {response.decode().strip()}")
            return True
        else:
            print("Board not responding - may have crashed")
            return False
    finally:
        ser.close()


if __name__ == "__main__":
    print("=== CRASH INVESTIGATION TEST ===")
    print("Watch the heartbeat LED during tests")
    print("If it stops flashing, the board has crashed\n")

    tests = [
        ("Rapid Commands", test_rapid_commands),
        ("Large Buffer", test_large_buffer),
        ("Incomplete Commands", test_incomplete_commands),
        ("Binary Data", test_binary_data),
        ("Mixed Line Endings", test_mixed_line_endings),
    ]

    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-" * 40)

        result = test_func()

        if not result:
            print(f"\n!!! CRASH DETECTED during {name} test !!!")
            print("Board needs to be reset")
            break

        # Wait between tests
        print("\nWaiting 3 seconds before next test...")
        time.sleep(3)

    print("\n=== TEST COMPLETE ===")
