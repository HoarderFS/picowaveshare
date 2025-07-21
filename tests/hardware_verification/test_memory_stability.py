"""
Memory Stability Test
Test the board with rapid commands to verify memory leak fixes
"""

import time

import serial
from waveshare_relay.discovery import find_relay_board


def test_rapid_commands(iterations=100):
    """Send many rapid commands to test stability"""
    print(f"=== RAPID COMMAND TEST ({iterations} iterations) ===")

    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    start_time = time.time()
    failures = 0

    try:
        for i in range(iterations):
            # Mix of different commands
            commands = ["PING", "STATUS", "ON 1", "OFF 1", "BEEP", "INFO", "UID"]

            cmd = commands[i % len(commands)]

            # Send command
            ser.reset_input_buffer()
            ser.write((cmd + "\n").encode())
            ser.flush()

            # Get response (with very short timeout)
            time.sleep(0.05)  # 50ms
            response = ser.readline()

            if not response:
                failures += 1
                print(f"Iteration {i + 1}: No response to {cmd}")
            elif i % 10 == 0:
                print(f"Iteration {i + 1}: {cmd} -> {response.decode().strip()}")

        elapsed = time.time() - start_time

        # Final check - is board still alive?
        ser.reset_input_buffer()
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(0.5)
        final_response = ser.readline()

        if final_response:
            print(f"\n✓ Board survived {iterations} commands in {elapsed:.2f}s")
            print(f"Failures: {failures}")
            return True
        else:
            print("\n✗ Board crashed after test")
            return False

    finally:
        ser.close()


def test_buzzer_stress():
    """Stress test buzzer operations which had PWM leak"""
    print("\n=== BUZZER STRESS TEST ===")

    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    try:
        for i in range(50):
            # Rapid buzzer on/off
            ser.write(b"BUZZ ON\n")
            ser.flush()
            time.sleep(0.1)

            ser.write(b"BUZZ OFF\n")
            ser.flush()
            time.sleep(0.1)

            if i % 10 == 0:
                # Check if still responsive
                ser.write(b"PING\n")
                ser.flush()
                time.sleep(0.1)
                response = ser.readline()
                if response:
                    print(f"Iteration {i}: Still alive")
                else:
                    print(f"Iteration {i}: Board not responding!")
                    return False

        print("✓ Buzzer stress test passed")
        return True

    finally:
        ser.close()


def test_memory_monitoring():
    """Monitor memory usage over time"""
    print("\n=== MEMORY MONITORING TEST ===")

    port = find_relay_board()
    if not port:
        print("No board found")
        return False

    # Note: This would require adding a MEM command to the protocol
    # For now, just run commands and watch for degradation

    ser = serial.Serial(port, 115200, timeout=2)
    time.sleep(1)

    try:
        baseline_time = None

        for i in range(20):
            start = time.time()

            # Send 10 rapid commands
            for _j in range(10):
                ser.write(b"STATUS\n")
                ser.flush()
                time.sleep(0.02)
                ser.readline()

            elapsed = time.time() - start

            if baseline_time is None:
                baseline_time = elapsed
                print(f"Batch {i + 1}: {elapsed:.3f}s (baseline)")
            else:
                diff = ((elapsed - baseline_time) / baseline_time) * 100
                print(f"Batch {i + 1}: {elapsed:.3f}s ({diff:+.1f}% from baseline)")

                # If response time degrades by more than 50%, memory might be leaking
                if diff > 50:
                    print("⚠️  Significant performance degradation detected")
                    return False

        print("✓ No significant performance degradation")
        return True

    finally:
        ser.close()


if __name__ == "__main__":
    print("=== MEMORY STABILITY TEST SUITE ===\n")

    tests = [
        ("Rapid Commands", lambda: test_rapid_commands(100)),
        ("Buzzer Stress", test_buzzer_stress),
        ("Memory Monitoring", test_memory_monitoring),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-" * 40)

        if test_func():
            passed += 1
        else:
            failed += 1
            print(f"❌ {name} failed - board may need reset")
            break

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 40}")
