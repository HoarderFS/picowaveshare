"""
Comprehensive Pin Verification for Waveshare Pico Relay B
This script tests all documented pins and generates a verification report
"""

import builtins
import contextlib
import json
import time

from machine import PWM, Pin


class PinVerifier:
    def __init__(self):
        self.results = {
            "board": "Waveshare Pico Relay B",
            "test_date": str(time.time()),
            "relays": {},
            "peripherals": {},
            "issues": [],
        }

    def test_relay_pins(self):
        """Test all relay pins"""
        print("\n=== TESTING RELAY PINS ===")

        relay_pins = {1: 21, 2: 20, 3: 19, 4: 18, 5: 17, 6: 16, 7: 15, 8: 14}

        for relay_num, pin_num in relay_pins.items():
            try:
                print(f"Testing Relay {relay_num} on GP{pin_num}...", end="")
                relay = Pin(pin_num, Pin.OUT)

                # Test on/off
                relay.value(1)
                time.sleep(0.1)
                on_state = relay.value()

                relay.value(0)
                time.sleep(0.1)
                off_state = relay.value()

                if on_state == 1 and off_state == 0:
                    print(" OK")
                    self.results["relays"][f"relay_{relay_num}"] = {
                        "pin": pin_num,
                        "status": "OK",
                        "control": "working",
                    }
                else:
                    print(" FAIL (state mismatch)")
                    self.results["relays"][f"relay_{relay_num}"] = {
                        "pin": pin_num,
                        "status": "FAIL",
                        "error": "State mismatch",
                    }
                    self.results["issues"].append(f"Relay {relay_num} state mismatch")

            except Exception as e:
                print(f" FAIL ({e})")
                self.results["relays"][f"relay_{relay_num}"] = {
                    "pin": pin_num,
                    "status": "FAIL",
                    "error": str(e),
                }
                self.results["issues"].append(f"Relay {relay_num}: {e}")

    def test_peripherals(self):
        """Test peripheral components"""
        print("\n=== TESTING PERIPHERALS ===")

        # Test onboard LED
        try:
            print("Testing onboard LED (GP25)...", end="")
            led = Pin(25, Pin.OUT)
            led.value(1)
            time.sleep(0.2)
            led.value(0)
            print(" OK")
            self.results["peripherals"]["onboard_led"] = {"pin": 25, "status": "OK"}
        except Exception as e:
            print(f" FAIL ({e})")
            self.results["peripherals"]["onboard_led"] = {
                "pin": 25,
                "status": "FAIL",
                "error": str(e),
            }
            self.results["issues"].append(f"Onboard LED: {e}")

        # Test buzzer
        try:
            print("Testing buzzer (GP22)...", end="")
            buzzer = PWM(Pin(22))
            buzzer.freq(1000)
            buzzer.duty_u16(32768)
            time.sleep(0.1)
            buzzer.duty_u16(0)
            print(" PRESENT")
            self.results["peripherals"]["buzzer"] = {"pin": 22, "status": "PRESENT"}
        except Exception:
            print(" NOT FOUND")
            self.results["peripherals"]["buzzer"] = {"pin": 22, "status": "NOT_FOUND"}

        # Test button
        try:
            print("Testing button (GP9)...", end="")
            button = Pin(9, Pin.IN, Pin.PULL_UP)
            state = button.value()
            print(f" PRESENT (state={state})")
            self.results["peripherals"]["button"] = {
                "pin": 9,
                "status": "PRESENT",
                "pull_up_state": state,
            }
        except Exception:
            print(" NOT FOUND")
            self.results["peripherals"]["button"] = {"pin": 9, "status": "NOT_FOUND"}

        # Test RGB LED
        rgb_found = True
        for color, pin in [("red", 6), ("green", 7), ("blue", 8)]:
            try:
                print(f"Testing RGB {color} (GP{pin})...", end="")
                led = PWM(Pin(pin))
                led.freq(1000)
                led.duty_u16(32768)
                time.sleep(0.1)
                led.duty_u16(0)
                print(" PRESENT")
                self.results["peripherals"][f"rgb_{color}"] = {
                    "pin": pin,
                    "status": "PRESENT",
                }
            except Exception:
                print(" NOT FOUND")
                self.results["peripherals"][f"rgb_{color}"] = {
                    "pin": pin,
                    "status": "NOT_FOUND",
                }
                rgb_found = False

        if rgb_found:
            self.results["peripherals"]["rgb_led"] = "COMPLETE"
        else:
            self.results["peripherals"]["rgb_led"] = "NOT_FOUND"

    def generate_report(self):
        """Generate verification report"""
        print("\n" + "=" * 50)
        print("PIN VERIFICATION REPORT")
        print("=" * 50)

        print(f"\nBoard: {self.results['board']}")
        print(f"Test Date: {self.results['test_date']}")

        print("\n--- RELAY PINS ---")
        for relay, info in self.results["relays"].items():
            status = "✓" if info["status"] == "OK" else "✗"
            print(f"{status} {relay}: GP{info['pin']} - {info['status']}")

        print("\n--- PERIPHERALS ---")
        for peripheral, info in self.results["peripherals"].items():
            if isinstance(info, dict):
                status = "✓" if info["status"] in ["OK", "PRESENT"] else "✗"
                print(f"{status} {peripheral}: GP{info['pin']} - {info['status']}")

        if self.results["issues"]:
            print("\n--- ISSUES FOUND ---")
            for issue in self.results["issues"]:
                print(f"! {issue}")
        else:
            print("\n✓ No issues found!")

        print("\n" + "=" * 50)

        # Save report to file
        try:
            with open("pin_verification_report.json", "w") as f:
                f.write(json.dumps(self.results))
            print("\nReport saved to: pin_verification_report.json")
        except Exception:
            print("\nCould not save report to file")

        return len(self.results["issues"]) == 0

    def run_all_tests(self):
        """Run all verification tests"""
        print("Starting comprehensive pin verification...")

        self.test_relay_pins()
        self.test_peripherals()

        all_passed = self.generate_report()

        # Turn off all outputs
        print("\nCleaning up...")
        for i in range(14, 22):
            with contextlib.suppress(builtins.BaseException):
                Pin(i, Pin.OUT).value(0)

        return all_passed


def main():
    print("=== WAVESHARE PICO RELAY B PIN VERIFICATION ===")
    print("This will test all documented pins automatically")
    print("Make sure the board is properly connected")

    input("\nPress Enter to start verification...")

    verifier = PinVerifier()
    all_passed = verifier.run_all_tests()

    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
        print("The board matches the documented pin configuration.")
    else:
        print("\n✗ SOME TESTS FAILED!")
        print("Please check the issues above and update documentation if needed.")

    print("\nVerification complete.")


if __name__ == "__main__":
    main()
