#!/usr/bin/env python3
"""
Basic control example for Waveshare Pico Relay B

This example demonstrates basic relay control operations
using the waveshare_relay library.
"""

import os
import sys

from waveshare_relay import RelayController, RelayError, find_relay_board

# Configuration
# Try to get port from environment variable, otherwise use auto-discovery
SERIAL_PORT = os.environ.get("RELAY_PORT") or find_relay_board()
BAUDRATE = 115200


def main():
    """Main example function"""
    print("=== Waveshare Pico Relay B - Basic Control Example ===")

    # Check if we found a port
    if not SERIAL_PORT:
        print("ERROR: No relay board found!")
        print("Please connect a board or set RELAY_PORT environment variable")
        print("Example: export RELAY_PORT=/dev/cu.usbmodem84401")
        return 1

    try:
        # Create controller instance
        print(f"Connecting to board at {SERIAL_PORT}...")
        controller = RelayController(SERIAL_PORT, BAUDRATE)

        # Connect to board
        print(f"Connecting to {SERIAL_PORT}...")
        controller.connect()
        print("Connected successfully!")

        # Test ping
        if controller.ping():
            print("Board responding to PING")
        else:
            print("Board not responding to PING")
            return

        # Get board information
        info = controller.get_info()
        print(f"Board: {info.get('board_name', 'Unknown')}")
        print(f"Version: {info.get('version', 'Unknown')}")
        print(f"Channels: {info.get('channels', 'Unknown')}")
        print(f"UID: {info.get('uid', 'Unknown')}")

        # Get initial status
        print("\nInitial relay status:")
        states = controller.get_status()
        for relay_num, state in states.items():
            print(f"  Relay {relay_num}: {'ON' if state else 'OFF'}")

        # Test individual relay control
        print("\nTesting individual relay control...")

        # Turn on relay 1
        print("Turning on relay 1...")
        controller.relay_on(1)

        # Turn on relay 2
        print("Turning on relay 2...")
        controller.relay_on(2)

        # Check status
        states = controller.get_status()
        print(f"Relay 1: {'ON' if states[1] else 'OFF'}")
        print(f"Relay 2: {'ON' if states[2] else 'OFF'}")

        # Turn off relay 1
        print("Turning off relay 1...")
        controller.relay_off(1)

        # Turn off relay 2
        print("Turning off relay 2...")
        controller.relay_off(2)

        # Test all relays
        print("\nTesting all relays...")
        print("Turning all relays ON...")
        controller.all_relays_on()

        print("Turning all relays OFF...")
        controller.all_relays_off()

        # Test binary pattern
        print("\nTesting binary pattern...")
        print("Setting pattern 10101010 (alternating relays)...")
        controller.set_relay_pattern("10101010")

        print("Setting pattern 01010101 (opposite alternating)...")
        controller.set_relay_pattern("01010101")

        print("Turning all relays off...")
        controller.all_relays_off()

        # Test pulse
        print("\nTesting pulse...")
        print("Pulsing relay 1 for 500ms...")
        controller.pulse_relay(1, 500)

        # Test buzzer
        print("\nTesting buzzer...")
        print("Short beep...")
        controller.beep()

        print("Long beep (300ms)...")
        controller.beep(300)

        print("Playing tone 1000Hz for 200ms...")
        controller.tone(1000, 200)

        # Test relay naming
        print("\nTesting relay naming...")
        controller.set_relay_name(1, "MAIN_LIGHT")
        controller.set_relay_name(2, "BACKUP_LIGHT")

        print(f"Relay 1 name: {controller.get_relay_name(1)}")
        print(f"Relay 2 name: {controller.get_relay_name(2)}")

        # Get comprehensive relay information
        print("\nComprehensive relay information:")
        relay_info = controller.get_relay_states_dict()
        for relay_num, info in relay_info.items():
            print(f"  Relay {relay_num}: {info['name']} - {info['state_str']}")

        # Final status
        print("\nFinal relay status:")
        states = controller.get_status()
        for relay_num, state in states.items():
            print(f"  Relay {relay_num}: {'ON' if state else 'OFF'}")

        # Disconnect
        controller.disconnect()
        print("\nDisconnected from board.")

    except RelayError as e:
        print(f"Relay error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
