"""
Main program for Waveshare Pico Relay B board.

Integrates RelayController and ProtocolParser to provide USB serial
protocol interface. Features watchdog timer for stability, heartbeat LED
for health monitoring, and automatic state restoration on boot.

Firmware Version: 1.1.0
"""

import gc
import select
import sys
import time

from config import FIRMWARE_VERSION, ONBOARD_LED_PIN
from machine import WDT, Pin
from protocol import ProtocolParser
from relay_controller import RelayController


def main():
    """
    Main program with heartbeat LED and USB serial protocol server.

    Features:
    - 8-second watchdog timer to prevent hangs
    - 2Hz heartbeat LED on GP25 for health monitoring
    - Non-blocking serial I/O with select.poll()
    - Periodic garbage collection every 10 commands
    - Automatic relay state restoration if enabled
    - Boot beep to indicate ready status

    The main loop:
    1. Feeds the watchdog every 100ms
    2. Updates heartbeat LED every 500ms
    3. Polls for serial input with 100ms timeout
    4. Processes complete commands when newline received
    5. Handles errors gracefully without crashing
    """
    # Minimal startup message to reduce memory usage
    print(f"PICO RELAY B v{FIRMWARE_VERSION} Ready")

    try:
        # Initialize watchdog timer (8 second timeout)
        wdt = WDT(timeout=8000)

        # Initialize heartbeat LED
        led = Pin(ONBOARD_LED_PIN, Pin.OUT)
        led_state = False
        last_heartbeat = time.ticks_ms()

        # Initialize components
        # Initialize components without print statements
        relay_ctrl = RelayController()
        protocol = ProtocolParser(relay_ctrl)

        # Boot beep to indicate readiness
        if relay_ctrl.buzzer:
            relay_ctrl.buzzer_beep(200)  # Boot beep

        # Ready for commands - minimal message
        # Commands: PING, INFO, UID, STATUS, ON/OFF <1-8>, ALL ON/OFF
        #           SET <pattern>, PULSE <relay> <ms>, BEEP, BUZZ ON/OFF

        # Simple USB serial command loop with error handling
        buffer = ""
        poll = select.poll()
        poll.register(sys.stdin, select.POLLIN)

        while True:
            try:
                # Feed watchdog
                wdt.feed()

                # Update heartbeat LED every 500ms (2Hz for active indication)
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, last_heartbeat) >= 500:
                    led_state = not led_state
                    led.value(led_state)
                    last_heartbeat = current_time

                # Check for available data (non-blocking)
                events = poll.poll(100)  # 100ms timeout

                if events:
                    # Read available data
                    char = sys.stdin.read(1)
                    if char:
                        if char == "\n" or char == "\r":
                            # Process complete line
                            if buffer:
                                try:
                                    response = protocol.process_command(buffer)
                                    print(response, end="")
                                    # Add small delay to prevent buffer overflow
                                    time.sleep_ms(10)
                                    # Trigger garbage collection periodically
                                    if protocol.command_count % 10 == 0:
                                        gc.collect()
                                except Exception as e:
                                    print(f"ERROR:PROCESSING:{e}\n")
                                buffer = ""
                        else:
                            buffer += char

            except KeyboardInterrupt:
                print("\nShutdown requested")
                break
            except Exception as e:
                # Log error but keep running
                print(f"ERROR:SERIAL:{e}\n")
                time.sleep(0.1)  # Brief delay before retrying

    except Exception as e:
        print("ERROR:", e)
        sys.print_exception(e)


# Auto-start when the module is loaded by MicroPython
# This ensures the server starts automatically on boot
main()
