"""
Hardware Verification Test: Relay Control
Tests each relay individually to verify pin assignments

Expected pin mapping:
Relay 1: GP21
Relay 2: GP20
Relay 3: GP19
Relay 4: GP18
Relay 5: GP17
Relay 6: GP16
Relay 7: GP15
Relay 8: GP14
"""

import builtins
import contextlib
import time

from machine import Pin

# Define expected relay pins
RELAY_PINS = {
    1: 21,  # GP21
    2: 20,  # GP20
    3: 19,  # GP19
    4: 18,  # GP18
    5: 17,  # GP17
    6: 16,  # GP16
    7: 15,  # GP15
    8: 14,  # GP14
}


def test_single_relay(relay_num, pin_num):
    """Test a single relay"""
    print(f"\nTesting Relay {relay_num} on GP{pin_num}")
    print("Initializing pin...")

    try:
        relay = Pin(pin_num, Pin.OUT)
        relay.value(0)  # Ensure it starts OFF

        print(f"Relay {relay_num}: Turning ON...")
        relay.value(1)
        print("You should hear a click and see the LED turn on")
        print("Press Enter to continue...")
        input()

        print(f"Relay {relay_num}: Turning OFF...")
        relay.value(0)
        print("You should hear another click and see the LED turn off")
        print("Press Enter to continue...")
        input()

        return True

    except Exception as e:
        print(f"ERROR testing relay {relay_num}: {e}")
        return False


def test_all_relays_sequence():
    """Test all relays in sequence"""
    print("\n=== RELAY SEQUENCE TEST ===")
    print("This will turn each relay on for 0.5 seconds in sequence")
    print("Press Enter to start...")
    input()

    relays = {}
    for relay_num, pin_num in RELAY_PINS.items():
        try:
            relays[relay_num] = Pin(pin_num, Pin.OUT)
            relays[relay_num].value(0)
        except Exception as e:
            print(f"ERROR initializing relay {relay_num}: {e}")
            return

    # Sequence test
    for i in range(3):  # Run 3 times
        print(f"\nSequence {i + 1}/3")
        for relay_num in range(1, 9):
            if relay_num in relays:
                relays[relay_num].value(1)
                print(f"Relay {relay_num} ON", end="")
                time.sleep(0.1)
                relays[relay_num].value(0)
                print(" -> OFF")
                time.sleep(0.1)

    print("\nSequence test complete!")


def test_all_on_off():
    """Test all relays on/off together"""
    print("\n=== ALL RELAYS ON/OFF TEST ===")
    print("This will turn all relays on, then off")
    print("Press Enter to start...")
    input()

    relays = {}
    for relay_num, pin_num in RELAY_PINS.items():
        try:
            relays[relay_num] = Pin(pin_num, Pin.OUT)
            relays[relay_num].value(0)
        except Exception as e:
            print(f"ERROR initializing relay {relay_num}: {e}")
            return

    print("Turning all relays ON...")
    for relay in relays.values():
        relay.value(1)

    print("All relays should be ON. Press Enter to turn OFF...")
    input()

    print("Turning all relays OFF...")
    for relay in relays.values():
        relay.value(0)

    print("All relays should be OFF.")


def main():
    print("=== WAVESHARE PICO RELAY B - RELAY PIN VERIFICATION ===")
    print("This test will verify each relay pin assignment")
    print("Make sure you can hear the relay clicks and see the LEDs")

    while True:
        print("\n--- Test Menu ---")
        print("1. Test relays individually (interactive)")
        print("2. Test relay sequence (automatic)")
        print("3. Test all relays on/off")
        print("4. Exit")

        choice = input("\nSelect test (1-4): ")

        if choice == "1":
            # Test each relay individually
            results = {}
            for relay_num, pin_num in RELAY_PINS.items():
                results[relay_num] = test_single_relay(relay_num, pin_num)

            # Summary
            print("\n=== TEST SUMMARY ===")
            for relay_num, passed in results.items():
                status = "PASS" if passed else "FAIL"
                print(f"Relay {relay_num} (GP{RELAY_PINS[relay_num]}): {status}")

        elif choice == "2":
            test_all_relays_sequence()

        elif choice == "3":
            test_all_on_off()

        elif choice == "4":
            print("Exiting...")
            # Make sure all relays are off before exiting
            for pin_num in RELAY_PINS.values():
                with contextlib.suppress(builtins.BaseException):
                    Pin(pin_num, Pin.OUT).value(0)
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
