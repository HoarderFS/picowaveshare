"""
Relay Controller for Waveshare Pico Relay B board.

Provides high-level interface for controlling 8 relays with buzzer support,
state persistence, and automatic state restoration on boot.

Features:
- Individual relay control (on/off)
- Bulk operations (all on/off, pattern setting)
- State tracking and validation
- Buzzer control with PWM (beep, tone, continuous)
- Automatic state restoration from persistent storage
- Watchdog-safe operation with timing limits
"""

import time

from config import (
    BUZZER_DUTY_OFF,
    BUZZER_DUTY_ON,
    BUZZER_FREQ_DEFAULT,
    BUZZER_PIN,
    DEBUG,
    DEFAULT_RELAY_STATE,
    RELAY_COUNT,
    RELAY_OFF,
    RELAY_ON,
    RELAY_PINS,
    RELAY_SETTLE_TIME,
    get_auto_load_enabled,
    is_valid_relay_number,
    load_relay_states,
)
from machine import PWM, Pin


class RelayController:
    """
    Controls 8 relays on the Waveshare Pico Relay B board.

    This class manages relay hardware control, state tracking, buzzer operations,
    and integrates with persistent storage for state restoration.

    Attributes:
        relays (dict): Mapping of relay numbers (1-8) to Pin objects
        relay_states (list): Current state of each relay (RELAY_ON or RELAY_OFF)
        buzzer (PWM): PWM object for buzzer control, None if initialization fails
        buzzer_active (bool): True if buzzer is currently active

    Note:
        - Relay numbers are 1-indexed (1-8) for user convenience
        - All timing operations are limited to prevent watchdog timeouts
        - PWM resources are properly managed to prevent exhaustion
    """

    def __init__(self):
        """
        Initialize relay controller and set all relays to OFF.

        Performs the following initialization:
        1. Initializes all 8 relay pins and sets them to OFF
        2. Initializes buzzer with PWM if available
        3. Checks for auto-load setting and restores saved states if enabled
        4. Plays a boot beep to indicate system is ready

        Raises:
            Exception: If relay pin initialization fails
        """
        self.relays = {}
        self.relay_states = [RELAY_OFF] * RELAY_COUNT
        self._initialize_relays()
        self._initialize_buzzer()

        # Check for auto-load of saved states
        if get_auto_load_enabled():
            saved_states = load_relay_states()
            if saved_states and saved_states != "00000000":  # Only load if not all zeros
                try:
                    self.set_states(saved_states)
                    if DEBUG:
                        print(f"Auto-loaded relay states: {saved_states}")
                except Exception as e:
                    if DEBUG:
                        print(f"Failed to auto-load relay states: {e}")

        # Boot beep to indicate system is ready
        if self.buzzer:
            self.buzzer_beep(150)  # Short boot beep

        if DEBUG:
            print("RelayController initialized")

    def _initialize_relays(self):
        """
        Initialize all relay pins and set to default state.

        Creates Pin objects for each relay and sets them to their default state
        (OFF). Allows RELAY_SETTLE_TIME after initialization for hardware to stabilize.

        Raises:
            Exception: If any relay pin fails to initialize
        """
        for relay_num, pin_num in RELAY_PINS.items():
            try:
                # Create Pin object with OUTPUT mode
                self.relays[relay_num] = Pin(pin_num, Pin.OUT)
                # Set to default state (OFF)
                self.relays[relay_num].value(DEFAULT_RELAY_STATE[relay_num - 1])
                self.relay_states[relay_num - 1] = DEFAULT_RELAY_STATE[relay_num - 1]

                if DEBUG:
                    print(f"Relay {relay_num} initialized on GP{pin_num}")

            except Exception as e:
                print(
                    f"ERROR: Failed to initialize relay {relay_num} on GP{pin_num}: {e}"
                )
                raise

        # Allow relays to settle
        time.sleep_ms(RELAY_SETTLE_TIME)

    def _initialize_buzzer(self):
        """
        Initialize buzzer with PWM.

        Sets up PWM on the buzzer pin with default frequency. If initialization
        fails, the buzzer is disabled but relay operations continue normally.

        Note:
            Buzzer is optional - failures are logged but don't stop initialization
        """
        try:
            self.buzzer = PWM(Pin(BUZZER_PIN))
            self.buzzer.freq(BUZZER_FREQ_DEFAULT)
            self.buzzer.duty_u16(BUZZER_DUTY_OFF)  # Start with buzzer off
            self.buzzer_active = False

            if DEBUG:
                print(f"Buzzer initialized on GP{BUZZER_PIN}")
        except Exception as e:
            print(f"ERROR: Failed to initialize buzzer on GP{BUZZER_PIN}: {e}")
            self.buzzer = None
            self.buzzer_active = False

    def relay_on(self, relay_num):
        """
        Turn on a specific relay.

        Args:
            relay_num (int): Relay number (1-8)

        Returns:
            bool: True if successful, False if relay number invalid or hardware error

        Note:
            Includes RELAY_SETTLE_TIME delay after state change
        """
        if not is_valid_relay_number(relay_num):
            if DEBUG:
                print(f"ERROR: Invalid relay number: {relay_num}")
            return False

        try:
            self.relays[relay_num].value(RELAY_ON)
            self.relay_states[relay_num - 1] = RELAY_ON

            if DEBUG:
                print(f"Relay {relay_num} turned ON")

            # Allow relay to settle
            time.sleep_ms(RELAY_SETTLE_TIME)
            return True

        except Exception as e:
            print(f"ERROR: Failed to turn on relay {relay_num}: {e}")
            return False

    def relay_off(self, relay_num):
        """
        Turn off a specific relay.

        Args:
            relay_num (int): Relay number (1-8)

        Returns:
            bool: True if successful, False if relay number invalid or hardware error

        Note:
            Includes RELAY_SETTLE_TIME delay after state change
        """
        if not is_valid_relay_number(relay_num):
            if DEBUG:
                print(f"ERROR: Invalid relay number: {relay_num}")
            return False

        try:
            self.relays[relay_num].value(RELAY_OFF)
            self.relay_states[relay_num - 1] = RELAY_OFF

            if DEBUG:
                print(f"Relay {relay_num} turned OFF")

            # Allow relay to settle
            time.sleep_ms(RELAY_SETTLE_TIME)
            return True

        except Exception as e:
            print(f"ERROR: Failed to turn off relay {relay_num}: {e}")
            return False


    def get_relay_state(self, relay_num):
        """
        Get the current state of a specific relay.

        Args:
            relay_num (int): Relay number (1-8)

        Returns:
            int or None: RELAY_ON (1) or RELAY_OFF (0) if valid relay,
                        None if relay number is invalid
        """
        if not is_valid_relay_number(relay_num):
            return None

        return self.relay_states[relay_num - 1]

    def get_all_states(self):
        """
        Get states of all relays.

        Returns:
            list: List of relay states [relay1, relay2, ..., relay8]
                  where each element is RELAY_ON (1) or RELAY_OFF (0)
        """
        return self.relay_states.copy()

    def get_status_binary(self):
        """
        Get relay states as 8-bit binary string.

        Used by the STATUS protocol command to return relay states in a
        compact binary format.

        Returns:
            str: 8-bit binary string (e.g., "10110000") where:
                 - MSB (leftmost bit) = relay 8
                 - LSB (rightmost bit) = relay 1
                 - '1' = relay ON, '0' = relay OFF
        """
        # Reverse the list so relay 8 is MSB
        # Use single list comprehension to minimize memory allocations
        return "".join(
            str(self.relay_states[i]) for i in range(len(self.relay_states) - 1, -1, -1)
        )

    def all_on(self):
        """
        Turn all relays ON.

        Attempts to turn on all 8 relays in sequence. If any relay fails,
        continues with remaining relays.

        Returns:
            bool: True if all relays turned on successfully,
                  False if any relay failed
        """
        success = True
        for relay_num in range(1, RELAY_COUNT + 1):
            if not self.relay_on(relay_num):
                success = False

        if DEBUG:
            print(f"All relays turned ON: {'SUCCESS' if success else 'SOME FAILED'}")

        return success

    def all_off(self):
        """
        Turn all relays OFF.

        Attempts to turn off all 8 relays in sequence. If any relay fails,
        continues with remaining relays.

        Returns:
            bool: True if all relays turned off successfully,
                  False if any relay failed
        """
        success = True
        for relay_num in range(1, RELAY_COUNT + 1):
            if not self.relay_off(relay_num):
                success = False

        if DEBUG:
            print(f"All relays turned OFF: {'SUCCESS' if success else 'SOME FAILED'}")

        return success

    def set_states(self, states):
        """
        Set relay states from a string pattern.

        This method is used by the LOAD command and auto-load feature to restore
        saved relay states. It converts from storage format to the format expected
        by set_pattern().

        Args:
            states (str): 8-character string of relay states where:
                         - states[0] corresponds to relay 1
                         - states[7] corresponds to relay 8
                         - '0' = relay OFF, '1' = relay ON
                         Example: "00110101" sets relays 3,4,6,8 ON

        Returns:
            bool: True if successful, False if invalid format

        Note:
            Internally reverses the string to match set_pattern's MSB-first format
        """
        # Convert from storage format (relay 1 first) to pattern format (relay 8 first)
        # Reverse the string to match set_pattern's expectation
        # MicroPython doesn't support [::-1], so reverse manually
        pattern = ''.join(reversed(states))
        return self.set_pattern(pattern)

    def set_pattern(self, pattern):
        """
        Set relay states according to binary pattern.

        Used by the SET protocol command to set multiple relays at once.

        Args:
            pattern (str): 8-bit binary string where:
                          - MSB (leftmost bit) = relay 8
                          - LSB (rightmost bit) = relay 1
                          - '1' = turn relay ON, '0' = turn relay OFF
                          Example: "10110000" sets relays 5,6,8 ON

        Returns:
            bool: True if pattern applied successfully,
                  False if invalid format or any relay failed
        """
        if not isinstance(pattern, str) or len(pattern) != 8:
            if DEBUG:
                print(f"ERROR: Invalid pattern format: {pattern}")
            return False

        # Validate pattern contains only 0s and 1s
        if not all(c in "01" for c in pattern):
            if DEBUG:
                print(f"ERROR: Pattern contains invalid characters: {pattern}")
            return False

        try:
            # Convert pattern to list of states
            # Pattern is MSB first, so reverse it
            # Use list comprehension to avoid string concatenation
            states = [int(pattern[i]) for i in range(len(pattern) - 1, -1, -1)]

            success = True
            for relay_num in range(1, RELAY_COUNT + 1):
                desired_state = states[relay_num - 1]

                if desired_state == RELAY_ON:
                    if not self.relay_on(relay_num):
                        success = False
                else:
                    if not self.relay_off(relay_num):
                        success = False

            if DEBUG:
                print(
                    f"Pattern {pattern} applied: {'SUCCESS' if success else 'SOME FAILED'}"
                )

            return success

        except Exception as e:
            print(f"ERROR: Failed to apply pattern {pattern}: {e}")
            return False

    def reset(self):
        """
        Reset all relays to OFF state.

        Convenience method that calls all_off().

        Returns:
            bool: True if all relays reset successfully,
                  False if any relay failed
        """
        if DEBUG:
            print("Resetting all relays to OFF")

        return self.all_off()

    def pulse_relay(self, relay_num, duration_ms):
        """
        Pulse a relay (turn on for specified duration then off).

        Used by the PULSE protocol command. After the pulse, the relay returns
        to its original state (not necessarily OFF).

        Args:
            relay_num (int): Relay number (1-8)
            duration_ms (int): Duration in milliseconds (max 5000ms for watchdog safety)

        Returns:
            bool: True if pulse completed successfully,
                  False if invalid parameters or hardware error

        Note:
            Duration is limited to 5 seconds to prevent watchdog timeouts
        """
        if not is_valid_relay_number(relay_num):
            if DEBUG:
                print(f"ERROR: Invalid relay number: {relay_num}")
            return False

        if duration_ms <= 0:
            if DEBUG:
                print(f"ERROR: Invalid duration: {duration_ms}")
            return False

        try:
            # Store original state
            original_state = self.relay_states[relay_num - 1]

            # Turn on
            if not self.relay_on(relay_num):
                return False

            # Wait for duration
            time.sleep_ms(duration_ms)

            # Return to original state
            if original_state == RELAY_ON:
                return self.relay_on(relay_num)
            else:
                return self.relay_off(relay_num)

        except Exception as e:
            print(f"ERROR: Failed to pulse relay {relay_num}: {e}")
            return False

    def get_info(self):
        """
        Get controller information.

        Provides a summary of the controller state for debugging.

        Returns:
            dict: Controller information containing:
                - relay_count: Number of relays (8)
                - relay_pins: GPIO pin mappings
                - current_states: List of current relay states
                - status_binary: Binary string representation
        """
        return {
            "relay_count": RELAY_COUNT,
            "relay_pins": RELAY_PINS,
            "current_states": self.relay_states.copy(),
            "status_binary": self.get_status_binary(),
        }

    def self_test(self):
        """
        Perform self-test of all relays.

        Tests each relay by turning it ON, verifying state, turning it OFF,
        and verifying state again. Useful for hardware verification.

        Returns:
            bool: True if all relays pass ON/OFF state verification,
                  False if any relay fails

        Note:
            This operation takes several seconds as each relay is tested
            individually with settle time delays
        """
        if DEBUG:
            print("Starting relay self-test...")

        success = True

        # Test each relay individually
        for relay_num in range(1, RELAY_COUNT + 1):
            if DEBUG:
                print(f"Testing relay {relay_num}...")

            # Test on
            if not self.relay_on(relay_num):
                success = False
                continue

            # Verify state
            if self.get_relay_state(relay_num) != RELAY_ON:
                if DEBUG:
                    print(f"ERROR: Relay {relay_num} state verification failed (ON)")
                success = False

            # Test off
            if not self.relay_off(relay_num):
                success = False
                continue

            # Verify state
            if self.get_relay_state(relay_num) != RELAY_OFF:
                if DEBUG:
                    print(f"ERROR: Relay {relay_num} state verification failed (OFF)")
                success = False

        if DEBUG:
            print(f"Self-test completed: {'PASSED' if success else 'FAILED'}")

        return success

    def buzzer_on(self, frequency=None):
        """
        Turn buzzer on at specified frequency.

        Used by the BUZZ ON protocol command for continuous buzzer operation.

        Args:
            frequency (int, optional): Frequency in Hz. If None, uses BUZZER_FREQ_DEFAULT

        Returns:
            bool: True if buzzer turned on successfully,
                  False if buzzer not available or error
        """
        if not self.buzzer:
            return False

        try:
            if frequency is None:
                frequency = BUZZER_FREQ_DEFAULT

            self.buzzer.freq(frequency)
            self.buzzer.duty_u16(BUZZER_DUTY_ON)
            self.buzzer_active = True

            if DEBUG:
                print(f"Buzzer ON at {frequency}Hz")
            return True
        except Exception as e:
            print(f"ERROR: Failed to turn buzzer on: {e}")
            return False

    def buzzer_off(self):
        """
        Turn buzzer off.

        Used by the BUZZ OFF protocol command. Properly releases PWM resources
        to prevent exhaustion during rapid on/off cycles.

        Returns:
            bool: True if buzzer turned off successfully,
                  False if buzzer not available or error

        Note:
            Deinitializes and reinitializes PWM to prevent resource leaks
        """
        if not self.buzzer:
            return False

        try:
            self.buzzer.duty_u16(BUZZER_DUTY_OFF)
            self.buzzer_active = False
            # Deinitialize PWM to free resources
            self.buzzer.deinit()
            # Recreate PWM for next use
            self.buzzer = PWM(Pin(BUZZER_PIN))
            self.buzzer.freq(BUZZER_FREQ_DEFAULT)
            self.buzzer.duty_u16(BUZZER_DUTY_OFF)

            if DEBUG:
                print("Buzzer OFF")
            return True
        except Exception as e:
            print(f"ERROR: Failed to turn buzzer off: {e}")
            return False

    def buzzer_beep(self, duration_ms=100, frequency=None):
        """
        Quick beep for notifications.

        Used by the BEEP protocol command and for boot/error notifications.

        Args:
            duration_ms (int): Beep duration in milliseconds (default 100ms)
            frequency (int, optional): Frequency in Hz. If None, uses default

        Returns:
            bool: True if beep completed successfully,
                  False if buzzer not available or error
        """
        if not self.buzzer:
            return False

        try:
            self.buzzer_on(frequency)
            time.sleep_ms(duration_ms)
            self.buzzer_off()
            return True
        except Exception as e:
            print(f"ERROR: Failed to beep: {e}")
            return False

    def buzzer_tone(self, frequency, duration_ms):
        """
        Play specific tone for duration.

        Used by the TONE protocol command to play arbitrary frequencies.

        Args:
            frequency (int): Frequency in Hz (50-20000 Hz range)
            duration_ms (int): Duration in milliseconds (max 5000ms)

        Returns:
            bool: True if tone played successfully,
                  False if buzzer not available or error

        Note:
            Duration limited to 5 seconds for watchdog safety
        """
        if not self.buzzer:
            return False

        try:
            self.buzzer_on(frequency)
            time.sleep_ms(duration_ms)
            self.buzzer_off()
            return True
        except Exception as e:
            print(f"ERROR: Failed to play tone: {e}")
            return False

    def get_buzzer_state(self):
        """
        Get current buzzer state.

        Returns:
            bool: True if buzzer is currently active, False otherwise
        """
        return self.buzzer_active if self.buzzer else False
