"""
Protocol encoder/decoder for Waveshare Pico Relay B ASCII protocol
"""

import re

from .exceptions import RelayValidationError


class RelayProtocol:
    """
    ASCII Protocol encoder/decoder for relay control commands

    Handles command formatting, validation, and response parsing
    for the Waveshare Pico Relay B board protocol.
    """

    # Protocol constants
    COMMAND_TERMINATOR = "\n"
    RESPONSE_TERMINATOR = "\n"
    MAX_COMMAND_LENGTH = 64

    # Valid relay numbers
    MIN_RELAY = 1
    MAX_RELAY = 8

    # Command parameter validation
    BEEP_MIN_DURATION = 1
    BEEP_MAX_DURATION = 5000
    PULSE_MIN_DURATION = 1
    PULSE_MAX_DURATION = 5000  # Max 5 seconds (watchdog safe)
    TONE_MIN_FREQUENCY = 50
    TONE_MAX_FREQUENCY = 20000
    TONE_MIN_DURATION = 1
    TONE_MAX_DURATION = 5000  # Max 5 seconds (watchdog safe)
    NAME_MAX_LENGTH = 32

    # Error code patterns
    ERROR_PATTERN = re.compile(r"^ERROR:(.+)$")

    def __init__(self):
        """Initialize protocol encoder/decoder"""
        pass

    def validate_relay_number(self, relay_num: int) -> bool:
        """Validate relay number is in valid range (1-8)"""
        return (
            isinstance(relay_num, int) and self.MIN_RELAY <= relay_num <= self.MAX_RELAY
        )

    def validate_binary_pattern(self, pattern: str) -> bool:
        """Validate 8-bit binary pattern"""
        return (
            isinstance(pattern, str)
            and len(pattern) == 8
            and all(c in "01" for c in pattern)
        )

    def encode_command(self, command: str, *args) -> str:
        """
        Encode a command with parameters into protocol format

        Args:
            command: Command name (e.g., 'ON', 'OFF', 'STATUS')
            *args: Command parameters

        Returns:
            str: Formatted command string ready to send

        Raises:
            RelayValidationError: If command or parameters are invalid
        """
        command = command.upper()

        # Validate and format based on command type
        if command == "PING":
            if args:
                raise RelayValidationError("PING command takes no parameters")
            return f"PING{self.COMMAND_TERMINATOR}"

        elif command == "ON":
            if len(args) != 1:
                raise RelayValidationError("ON command requires exactly one parameter")
            relay_num = args[0]
            if not self.validate_relay_number(relay_num):
                raise RelayValidationError(f"Invalid relay number: {relay_num}")
            return f"ON {relay_num}{self.COMMAND_TERMINATOR}"

        elif command == "OFF":
            if len(args) != 1:
                raise RelayValidationError("OFF command requires exactly one parameter")
            relay_num = args[0]
            if not self.validate_relay_number(relay_num):
                raise RelayValidationError(f"Invalid relay number: {relay_num}")
            return f"OFF {relay_num}{self.COMMAND_TERMINATOR}"

        elif command == "STATUS":
            if args:
                raise RelayValidationError("STATUS command takes no parameters")
            return f"STATUS{self.COMMAND_TERMINATOR}"

        elif command == "ALL":
            if len(args) != 1:
                raise RelayValidationError("ALL command requires exactly one parameter")
            operation = str(args[0]).upper()
            if operation not in ["ON", "OFF"]:
                raise RelayValidationError(
                    f"ALL command parameter must be ON or OFF, got: {operation}"
                )
            return f"ALL {operation}{self.COMMAND_TERMINATOR}"

        elif command == "SET":
            if len(args) != 1:
                raise RelayValidationError("SET command requires exactly one parameter")
            pattern = str(args[0])
            if not self.validate_binary_pattern(pattern):
                raise RelayValidationError(f"Invalid binary pattern: {pattern}")
            return f"SET {pattern}{self.COMMAND_TERMINATOR}"

        elif command == "PULSE":
            if len(args) != 2:
                raise RelayValidationError(
                    "PULSE command requires exactly two parameters"
                )
            relay_num, duration_ms = args
            if not self.validate_relay_number(relay_num):
                raise RelayValidationError(f"Invalid relay number: {relay_num}")
            if not isinstance(duration_ms, int) or not (
                self.PULSE_MIN_DURATION <= duration_ms <= self.PULSE_MAX_DURATION
            ):
                raise RelayValidationError(
                    f"Invalid duration: {duration_ms} (must be {self.PULSE_MIN_DURATION}-{self.PULSE_MAX_DURATION}ms)"
                )
            return f"PULSE {relay_num} {duration_ms}{self.COMMAND_TERMINATOR}"

        elif command == "INFO":
            if args:
                raise RelayValidationError("INFO command takes no parameters")
            return f"INFO{self.COMMAND_TERMINATOR}"

        elif command == "UID":
            if args:
                raise RelayValidationError("UID command takes no parameters")
            return f"UID{self.COMMAND_TERMINATOR}"

        elif command == "NAME":
            if len(args) not in [1, 2]:
                raise RelayValidationError(
                    "NAME command requires 1 or 2 parameters"
                )
            relay_num = args[0]
            if not self.validate_relay_number(relay_num):
                raise RelayValidationError(f"Invalid relay number: {relay_num}")
            
            if len(args) == 1:
                # Clear name - just relay number
                return f"NAME {relay_num}{self.COMMAND_TERMINATOR}"
            else:
                # Set name
                name = args[1]
                if (
                    not isinstance(name, str)
                    or len(name) == 0
                    or len(name) > self.NAME_MAX_LENGTH
                ):
                    raise RelayValidationError(
                        f"Invalid name: {name} (must be 1-{self.NAME_MAX_LENGTH} characters)"
                    )
                return f"NAME {relay_num} {name}{self.COMMAND_TERMINATOR}"

        elif command == "GET":
            if len(args) != 2:
                raise RelayValidationError(
                    "GET command requires exactly two parameters"
                )
            subcommand, relay_num = args
            if str(subcommand).upper() != "NAME":
                raise RelayValidationError(
                    f"GET subcommand must be NAME, got: {subcommand}"
                )
            if not self.validate_relay_number(relay_num):
                raise RelayValidationError(f"Invalid relay number: {relay_num}")
            return f"GET NAME {relay_num}{self.COMMAND_TERMINATOR}"

        elif command == "BEEP":
            if len(args) == 0:
                return f"BEEP{self.COMMAND_TERMINATOR}"
            elif len(args) == 1:
                duration_ms = args[0]
                if not isinstance(duration_ms, int) or not (
                    self.BEEP_MIN_DURATION <= duration_ms <= self.BEEP_MAX_DURATION
                ):
                    raise RelayValidationError(
                        f"Invalid beep duration: {duration_ms} (must be {self.BEEP_MIN_DURATION}-{self.BEEP_MAX_DURATION}ms)"
                    )
                return f"BEEP {duration_ms}{self.COMMAND_TERMINATOR}"
            else:
                raise RelayValidationError("BEEP command takes 0 or 1 parameters")

        elif command == "BUZZ":
            if len(args) != 1:
                raise RelayValidationError(
                    "BUZZ command requires exactly one parameter"
                )
            operation = str(args[0]).upper()
            if operation not in ["ON", "OFF"]:
                raise RelayValidationError(
                    f"BUZZ command parameter must be ON or OFF, got: {operation}"
                )
            return f"BUZZ {operation}{self.COMMAND_TERMINATOR}"

        elif command == "TONE":
            if len(args) != 2:
                raise RelayValidationError(
                    "TONE command requires exactly two parameters"
                )
            frequency, duration_ms = args
            if not isinstance(frequency, int) or not (
                self.TONE_MIN_FREQUENCY <= frequency <= self.TONE_MAX_FREQUENCY
            ):
                raise RelayValidationError(
                    f"Invalid frequency: {frequency} (must be {self.TONE_MIN_FREQUENCY}-{self.TONE_MAX_FREQUENCY}Hz)"
                )
            if not isinstance(duration_ms, int) or not (
                self.TONE_MIN_DURATION <= duration_ms <= self.TONE_MAX_DURATION
            ):
                raise RelayValidationError(
                    f"Invalid duration: {duration_ms} (must be {self.TONE_MIN_DURATION}-{self.TONE_MAX_DURATION}ms)"
                )
            return f"TONE {frequency} {duration_ms}{self.COMMAND_TERMINATOR}"

        elif command == "VERSION":
            if args:
                raise RelayValidationError("VERSION command takes no parameters")
            return f"VERSION{self.COMMAND_TERMINATOR}"

        elif command == "HELP":
            if args:
                raise RelayValidationError("HELP command takes no parameters")
            return f"HELP{self.COMMAND_TERMINATOR}"

        elif command == "SAVE":
            if args:
                raise RelayValidationError("SAVE command takes no parameters")
            return f"SAVE{self.COMMAND_TERMINATOR}"

        elif command == "LOAD":
            if args:
                raise RelayValidationError("LOAD command takes no parameters")
            return f"LOAD{self.COMMAND_TERMINATOR}"

        elif command == "CLEAR":
            if args:
                raise RelayValidationError("CLEAR command takes no parameters")
            return f"CLEAR{self.COMMAND_TERMINATOR}"

        else:
            raise RelayValidationError(f"Unknown command: {command}")

    def decode_response(self, response: str) -> tuple[bool, str | None, str | None]:
        """
        Decode a response from the relay board

        Args:
            response: Raw response string from board

        Returns:
            Tuple of (is_success, data, error_code)
            - is_success: True if command succeeded, False if error
            - data: Response data if successful, None if error
            - error_code: Error code if failed, None if successful
        """
        # Remove terminator and whitespace
        response = response.strip()

        # Check for error response
        error_match = self.ERROR_PATTERN.match(response)
        if error_match:
            error_code = error_match.group(1)
            return False, None, error_code

        # Success response
        if response == "OK":
            return True, None, None
        elif response == "PONG":
            return True, "PONG", None
        elif response in ["SAVED", "LOADED", "CLEARED"]:
            # State persistence responses
            return True, response, None
        else:
            # Response with data
            return True, response, None

    def parse_status_response(self, status_data: str) -> dict[int, bool]:
        """
        Parse STATUS command response into relay states

        Args:
            status_data: 8-bit binary string (e.g., "10101010")

        Returns:
            Dict mapping relay numbers (1-8) to boolean states
        """
        if not self.validate_binary_pattern(status_data):
            raise RelayValidationError(f"Invalid status data: {status_data}")

        # Convert binary string to relay states
        # MSB = relay 8, LSB = relay 1
        relay_states = {}
        for i in range(8):
            relay_num = i + 1
            bit_position = 7 - i  # MSB first
            relay_states[relay_num] = status_data[bit_position] == "1"

        return relay_states

    def parse_info_response(self, info_data: str) -> dict[str, str]:
        """
        Parse INFO command response into structured data

        Args:
            info_data: INFO response string

        Returns:
            Dict with parsed information
        """
        # Expected format: "WAVESHARE-PICO-RELAY-B,V1.0,8CH,UID:xxxxx"
        parts = info_data.split(",")
        info = {}

        if len(parts) >= 1:
            info["board_name"] = parts[0]
        if len(parts) >= 2:
            info["version"] = parts[1]
        if len(parts) >= 3:
            info["channels"] = parts[2]
        if len(parts) >= 4 and parts[3].startswith("UID:"):
            info["uid"] = parts[3][4:]  # Remove 'UID:' prefix

        return info
