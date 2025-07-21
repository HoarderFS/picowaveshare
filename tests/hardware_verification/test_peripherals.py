"""
Hardware Verification Test: Peripheral Components
Tests onboard LED, buzzer, button, and RGB LED (if present)

Expected components:
- Onboard LED: GP25 (always present on Pico)
- Buzzer: GP22 (if present)
- User Button: GP9 (if present, active LOW)
- RGB LED: GP6 (R), GP7 (G), GP8 (B) (if present)
"""

import time

from machine import PWM, Pin


def test_onboard_led():
    """Test the Pico's onboard LED"""
    print("\n=== TESTING ONBOARD LED (GP25) ===")
    print("The onboard LED should blink 5 times")

    try:
        led = Pin(25, Pin.OUT)
        for i in range(5):
            led.value(1)
            print(f"LED ON ({i + 1}/5)")
            time.sleep(0.5)
            led.value(0)
            print("LED OFF")
            time.sleep(0.5)
        print("Onboard LED test: PASS")
        return True
    except Exception as e:
        print(f"Onboard LED test: FAIL - {e}")
        return False


def test_buzzer():
    """Test buzzer if present"""
    print("\n=== TESTING BUZZER (GP22) ===")
    print("If buzzer is present, you should hear different tones")

    try:
        buzzer = PWM(Pin(22))

        # Test different frequencies
        frequencies = [500, 1000, 2000, 1000, 500]
        print("Playing tone sequence...")

        for freq in frequencies:
            buzzer.freq(freq)
            buzzer.duty_u16(32768)  # 50% duty cycle
            print(f"Frequency: {freq}Hz")
            time.sleep(0.2)

        buzzer.duty_u16(0)  # Turn off

        response = input("Did you hear the buzzer? (y/n): ")
        if response.lower() == "y":
            print("Buzzer test: PASS")
            return True
        else:
            print("Buzzer test: NOT PRESENT or FAIL")
            return False

    except Exception as e:
        print(f"Buzzer test: NOT PRESENT - {e}")
        return False


def test_button():
    """Test user button if present"""
    print("\n=== TESTING USER BUTTON (GP9) ===")
    print("If button is present, press it when prompted")

    try:
        button = Pin(9, Pin.IN, Pin.PULL_UP)

        # Check initial state
        initial_state = button.value()
        print(f"Button initial state: {'HIGH' if initial_state else 'LOW'}")

        print("\nPress and hold the button for 3 seconds...")

        button_pressed = False
        start_time = time.time()

        while time.time() - start_time < 5:  # 5 second timeout
            if button.value() == 0:  # Active LOW
                if not button_pressed:
                    print("Button PRESSED!")
                    button_pressed = True
            else:
                if button_pressed:
                    print("Button RELEASED!")
                    button_pressed = False
            time.sleep(0.1)

        if button_pressed or (initial_state == 1 and button.value() == 0):
            print("Button test: PASS")
            return True
        else:
            print("Button test: NOT PRESENT or not pressed")
            return False

    except Exception as e:
        print(f"Button test: NOT PRESENT - {e}")
        return False


def test_rgb_led():
    """Test RGB LED if present"""
    print("\n=== TESTING RGB LED (GP6,7,8) ===")
    print("If RGB LED is present, you should see different colors")

    try:
        # Initialize RGB channels
        red = PWM(Pin(6))
        green = PWM(Pin(7))
        blue = PWM(Pin(8))

        # Set frequency
        for led in [red, green, blue]:
            led.freq(1000)
            led.duty_u16(0)  # Start off

        # Test each color
        colors = [
            ("RED", red, 65535),
            ("GREEN", green, 65535),
            ("BLUE", blue, 65535),
            ("WHITE", None, None),  # All on
            ("OFF", None, None),  # All off
        ]

        for color_name, led, duty in colors:
            print(f"\nShowing: {color_name}")

            if color_name == "WHITE":
                red.duty_u16(65535)
                green.duty_u16(65535)
                blue.duty_u16(65535)
            elif color_name == "OFF":
                red.duty_u16(0)
                green.duty_u16(0)
                blue.duty_u16(0)
            else:
                # Turn off all first
                red.duty_u16(0)
                green.duty_u16(0)
                blue.duty_u16(0)
                # Turn on selected color
                if led:
                    led.duty_u16(duty)

            time.sleep(1)

        # Turn off
        for led in [red, green, blue]:
            led.duty_u16(0)

        response = input("\nDid you see the RGB LED colors? (y/n): ")
        if response.lower() == "y":
            print("RGB LED test: PASS")
            return True
        else:
            print("RGB LED test: NOT PRESENT or FAIL")
            return False

    except Exception as e:
        print(f"RGB LED test: NOT PRESENT - {e}")
        return False


def test_rgb_led_fade():
    """Test RGB LED with fade effect"""
    print("\n=== RGB LED FADE TEST ===")

    try:
        red = PWM(Pin(6))
        green = PWM(Pin(7))
        blue = PWM(Pin(8))

        for led in [red, green, blue]:
            led.freq(1000)

        print("Fading through colors...")

        # Fade through colors
        for i in range(256):
            red.duty_u16(i * 256)
            green.duty_u16((255 - i) * 256)
            blue.duty_u16((i // 2) * 256)
            time.sleep(0.01)

        # Turn off
        for led in [red, green, blue]:
            led.duty_u16(0)

        return True

    except Exception:
        return False


def main():
    print("=== WAVESHARE PICO RELAY B - PERIPHERAL VERIFICATION ===")
    print("This test will check for optional peripheral components")

    results = {
        "Onboard LED (GP25)": False,
        "Buzzer (GP22)": False,
        "User Button (GP9)": False,
        "RGB LED (GP6,7,8)": False,
    }

    while True:
        print("\n--- Peripheral Test Menu ---")
        print("1. Test onboard LED")
        print("2. Test buzzer")
        print("3. Test user button")
        print("4. Test RGB LED")
        print("5. Test RGB LED fade")
        print("6. Run all tests")
        print("7. Show results")
        print("8. Exit")

        choice = input("\nSelect test (1-8): ")

        if choice == "1":
            results["Onboard LED (GP25)"] = test_onboard_led()
        elif choice == "2":
            results["Buzzer (GP22)"] = test_buzzer()
        elif choice == "3":
            results["User Button (GP9)"] = test_button()
        elif choice == "4":
            results["RGB LED (GP6,7,8)"] = test_rgb_led()
        elif choice == "5":
            test_rgb_led_fade()
        elif choice == "6":
            # Run all tests
            results["Onboard LED (GP25)"] = test_onboard_led()
            results["Buzzer (GP22)"] = test_buzzer()
            results["User Button (GP9)"] = test_button()
            results["RGB LED (GP6,7,8)"] = test_rgb_led()
        elif choice == "7":
            print("\n=== PERIPHERAL TEST RESULTS ===")
            for component, passed in results.items():
                status = "PRESENT" if passed else "NOT FOUND"
                print(f"{component}: {status}")
        elif choice == "8":
            print("Exiting...")
            # Make sure everything is off
            try:
                Pin(25, Pin.OUT).value(0)  # Onboard LED
                PWM(Pin(22)).duty_u16(0)  # Buzzer
                PWM(Pin(6)).duty_u16(0)  # RGB Red
                PWM(Pin(7)).duty_u16(0)  # RGB Green
                PWM(Pin(8)).duty_u16(0)  # RGB Blue
            except Exception:
                pass
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
