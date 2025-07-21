"""
Hardware Verification Test: UART Communication
Tests UART on GP0 (TX) and GP1 (RX)

To test:
1. Run this script on the Pico
2. Connect via serial terminal (PuTTY, screen, etc.)
3. The script will echo back what you type
"""

import sys
import time

from machine import UART, Pin


def test_uart_echo():
    """Simple UART echo test"""
    print("\n=== UART ECHO TEST ===")
    print("Setting up UART on GP0 (TX) and GP1 (RX)")

    try:
        # Initialize UART
        uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

        print(f"UART initialized: {uart}")
        print("Type messages and they will be echoed back")
        print("Type 'exit' to stop the echo test")
        print("-" * 40)

        # Echo loop
        while True:
            if uart.any():
                data = uart.read()
                if data:
                    # Decode and echo back
                    try:
                        message = data.decode("utf-8")
                        print(f"Received: {message.strip()}")

                        # Echo back with prefix
                        response = f"Echo: {message}"
                        uart.write(response.encode("utf-8"))

                        # Check for exit command
                        if message.strip().lower() == "exit":
                            print("Exiting echo test...")
                            break
                    except Exception:
                        # If decode fails, show hex
                        hex_data = " ".join([f"{b:02x}" for b in data])
                        print(f"Received (hex): {hex_data}")
                        uart.write(b"Echo (hex): " + data)

            time.sleep(0.01)

        return True

    except Exception as e:
        print(f"UART test failed: {e}")
        return False


def test_uart_speeds():
    """Test different baud rates"""
    print("\n=== UART BAUD RATE TEST ===")

    baud_rates = [9600, 19200, 38400, 57600, 115200]
    results = {}

    for baud in baud_rates:
        print(f"\nTesting {baud} baud...")
        try:
            uart = UART(0, baudrate=baud, tx=Pin(0), rx=Pin(1))

            # Send test message
            test_msg = f"Testing at {baud} baud\n"
            uart.write(test_msg.encode("utf-8"))

            # Wait a bit
            time.sleep(0.1)

            # Check if we can read back (loopback test would need TX-RX connected)
            print(f"UART at {baud} baud: Initialized OK")
            results[baud] = True

        except Exception as e:
            print(f"UART at {baud} baud: FAILED - {e}")
            results[baud] = False

    # Reset to default
    uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

    return results


def test_uart_protocol_commands():
    """Test protocol-like commands"""
    print("\n=== UART PROTOCOL COMMAND TEST ===")
    print("This simulates protocol commands")

    try:
        uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

        print("Enter commands (ON 1, OFF 1, STATUS, PING, EXIT):")
        print("-" * 40)

        buffer = ""

        while True:
            if uart.any():
                data = uart.read()
                if data:
                    try:
                        # Add to buffer
                        buffer += data.decode("utf-8")

                        # Check for newline
                        if "\n" in buffer or "\r" in buffer:
                            # Process command
                            lines = buffer.replace("\r", "\n").split("\n")
                            for line in lines[:-1]:  # Process all complete lines
                                line = line.strip()
                                if line:
                                    print(f"Command: {line}")

                                    # Parse command
                                    parts = line.upper().split()
                                    if not parts:
                                        continue

                                    cmd = parts[0]

                                    # Simulate responses
                                    if cmd == "PING":
                                        response = "PONG\n"
                                    elif cmd == "STATUS":
                                        response = "00000000\n"  # All relays off
                                    elif (
                                        cmd == "ON"
                                        and len(parts) > 1
                                        or cmd == "OFF"
                                        and len(parts) > 1
                                    ):
                                        response = "OK\n"
                                    elif cmd == "EXIT":
                                        response = "BYE\n"
                                        uart.write(response.encode("utf-8"))
                                        print("Exiting protocol test...")
                                        return True
                                    else:
                                        response = "ERROR:INVALID_COMMAND\n"

                                    # Send response
                                    uart.write(response.encode("utf-8"))
                                    print(f"Response: {response.strip()}")

                            # Keep last incomplete line
                            buffer = lines[-1]

                    except Exception as e:
                        print(f"Error processing command: {e}")
                        buffer = ""

            time.sleep(0.01)

    except Exception as e:
        print(f"Protocol test failed: {e}")
        return False


def main():
    print("=== WAVESHARE PICO RELAY B - UART VERIFICATION ===")
    print("Default UART pins: GP0 (TX), GP1 (RX)")
    print("Default baud rate: 115200")

    # Show current REPL info
    print(f"\nCurrent stdin: {sys.stdin}")
    print(f"Current stdout: {sys.stdout}")

    while True:
        print("\n--- UART Test Menu ---")
        print("1. Echo test (type and receive echo)")
        print("2. Baud rate test")
        print("3. Protocol command test")
        print("4. Exit")

        choice = input("\nSelect test (1-4): ")

        if choice == "1":
            test_uart_echo()
        elif choice == "2":
            results = test_uart_speeds()
            print("\n=== BAUD RATE TEST RESULTS ===")
            for baud, passed in results.items():
                status = "PASS" if passed else "FAIL"
                print(f"{baud} baud: {status}")
        elif choice == "3":
            test_uart_protocol_commands()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice")

    print("\nUART verification complete")


if __name__ == "__main__":
    main()
