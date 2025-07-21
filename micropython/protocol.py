"""
ASCII Protocol Implementation for Waveshare Pico Relay B board.

Handles command parsing, validation, execution, and response formatting for
all supported protocol commands. Integrates with RelayController for hardware
control and persistent storage for configuration management.

Protocol Version: 1.0
Firmware Version: 1.1.0
"""

import time

from config import (
    BOARD_NAME,
    BOARD_VERSION,
    DEBUG,
    DEBUG_COMMANDS,
    ERROR_CODES,
    FIRMWARE_VERSION,
    PING_RESPONSE,
    PROTOCOL_VERSION,
    RELAY_COUNT,
    RESPONSE_TERMINATOR,
    SUCCESS_RESPONSE,
    clear_relay_states,
    get_board_info,
    get_board_uid,
    get_relay_name,
    is_valid_relay_number,
    load_relay_states,
    save_relay_states,
    set_relay_name,
)


class ProtocolParser:
    """
    ASCII Protocol Parser for relay control commands.

    Implements a text-based protocol for controlling the Waveshare Pico Relay B
    board over USB serial connection. All commands are case-insensitive and
    terminated with newline (\n).

    Command Format:
        <COMMAND> [PARAMETERS]\n
    Supported Commands:
        Relay Control:
        - ON <relay>            Turn on relay (1-8)
        - OFF <relay>           Turn off relay (1-8)
        - ALL ON/OFF            Turn all relays on or off
        - SET <pattern>         Set relay pattern (8-bit binary, MSB=relay8)
        - PULSE <relay> <ms>    Pulse relay for duration (max 5000ms)

        Query Commands:
        - STATUS                Get all relay states (8-bit binary)
        - PING                  Connection test (returns PONG)
        - INFO                  Get board info with UID
        - UID                   Get unique identifier only
        - VERSION               Get firmware version
        - HELP                  List available commands
        - GET NAME <relay>      Get relay name

        Configuration:
        - NAME <relay> <name>   Set persistent relay name (max 32 chars)
        - SAVE                  Save current relay states
        - LOAD                  Load saved relay states
        - CLEAR                 Clear saved relay states

        Buzzer Control:
        - BEEP [ms]             Short beep (default 100ms, max 5000ms)
        - BUZZ ON/OFF           Continuous buzzer on/off
        - TONE <hz> <ms>        Play tone (50-20000Hz, max 5000ms)

    Attributes:
        relay_controller: RelayController instance for hardware control
        command_count: Total commands processed
        error_count: Total errors encountered
        last_command_time: Timestamp of last command (ticks_ms)
    """

    def __init__(self, relay_controller=None):
        """
        Initialize protocol parser.

        Args:
            relay_controller: RelayController instance for hardware control.
                            If None, only validation is performed.
        """
        self.relay_controller = relay_controller
        self.command_count = 0
        self.error_count = 0
        self.last_command_time = 0

        if DEBUG:
            print("ProtocolParser initialized")

    def parse_command(self, command_str):
        """
        Parse a command string into command and parameters.

        Strips whitespace, converts to uppercase, and splits into command
        and parameter components.

        Args:
            command_str (str): Raw command string from serial input

        Returns:
            tuple: (command, parameters_list) where:
                - command is uppercase string or None if empty
                - parameters_list is list of parameter strings
        """
        # Remove leading/trailing whitespace and convert to uppercase
        command_str = command_str.strip().upper()

        if not command_str:
            return None, None

        # Split into command and parameters
        parts = command_str.split()
        command = parts[0] if parts else None
        parameters = parts[1:] if len(parts) > 1 else []

        if DEBUG_COMMANDS:
            print(f"Parsed command: '{command}', parameters: {parameters}")

        return command, parameters

    def validate_command(self, command, parameters):
        """
        Validate command and parameters.

        Checks command is recognized and has correct number and type of
        parameters. Performs range validation for numeric parameters.

        Args:
            command (str): Uppercase command name
            parameters (list): List of parameter strings

        Returns:
            tuple: (is_valid, error_code) where:
                - is_valid is True if command is valid
                - error_code is string error code if invalid, None if valid
        """
        if not command:
            return False, "EMPTY_COMMAND"

        # Define expected parameter counts for each command
        expected_params = {
            "ON": 1,
            "OFF": 1,
            "STATUS": 0,
            "PING": 0,
            "ALL": 1,  # ALL ON or ALL OFF
            "SET": 1,  # SET <8-bit binary>
            "PULSE": 2,  # PULSE <relay_number> <duration_ms>
            "INFO": 0,  # INFO - board information
            "UID": 0,  # UID - unique identifier
            "NAME": [1, 2],  # NAME <relay_number> [<name>]
            "GET": 2,  # GET NAME <relay_number>
            "BEEP": [0, 1],  # BEEP or BEEP <duration_ms>
            "BUZZ": 1,  # BUZZ ON or BUZZ OFF
            "TONE": 2,  # TONE <frequency_hz> <duration_ms>
            "VERSION": 0,  # VERSION - firmware version
            "HELP": 0,  # HELP - list available commands
            "SAVE": 0,  # SAVE - save current relay states
            "LOAD": 0,  # LOAD - load saved relay states
            "CLEAR": 0,  # CLEAR - clear saved relay states
        }

        # Check if command is supported
        if command not in expected_params:
            return False, "INVALID_COMMAND"

        # Check parameter count
        expected_count = expected_params[command]
        if isinstance(expected_count, list):
            # Variable parameter count (e.g., BEEP)
            if len(parameters) not in expected_count:
                return False, "INVALID_PARAMETER_COUNT"
        else:
            # Fixed parameter count
            if len(parameters) != expected_count:
                return False, "INVALID_PARAMETER_COUNT"

        # Validate parameters for relay commands
        if command in ["ON", "OFF"]:
            try:
                relay_num = int(parameters[0])
                if not is_valid_relay_number(relay_num):
                    return False, "INVALID_RELAY_NUMBER"
            except ValueError:
                return False, "INVALID_RELAY_NUMBER"

        # Validate parameters for ALL commands
        if command == "ALL" and parameters[0].upper() not in ["ON", "OFF"]:
            return False, "INVALID_PARAMETER"

        # Validate parameters for SET command
        if command == "SET":
            pattern = parameters[0]
            if len(pattern) != 8 or not all(c in "01" for c in pattern):
                return False, "INVALID_PARAMETER"

        # Validate parameters for PULSE command
        if command == "PULSE":
            try:
                relay_num = int(parameters[0])
                if not is_valid_relay_number(relay_num):
                    return False, "INVALID_RELAY_NUMBER"
                duration_ms = int(parameters[1])
                if (
                    duration_ms <= 0 or duration_ms > 5000
                ):  # Max 5 seconds (watchdog safe)
                    return False, "INVALID_PARAMETER"
            except ValueError:
                return False, "INVALID_PARAMETER"

        # Validate parameters for NAME command
        if command == "NAME":
            try:
                relay_num = int(parameters[0])
                if not is_valid_relay_number(relay_num):
                    return False, "INVALID_RELAY_NUMBER"
                # If name is provided, validate it
                if len(parameters) == 2:
                    name = parameters[1]
                    if not isinstance(name, str) or len(name) > 32:
                        return False, "INVALID_PARAMETER"
            except ValueError:
                return False, "INVALID_RELAY_NUMBER"

        # Validate parameters for GET NAME command
        if command == "GET":
            if parameters[0].upper() != "NAME":
                return False, "INVALID_PARAMETER"
            try:
                relay_num = int(parameters[1])
                if not is_valid_relay_number(relay_num):
                    return False, "INVALID_RELAY_NUMBER"
            except ValueError:
                return False, "INVALID_RELAY_NUMBER"

        # Validate parameters for BEEP command
        if command == "BEEP" and len(parameters) == 1:
            try:
                duration_ms = int(parameters[0])
                if duration_ms <= 0 or duration_ms > 5000:  # Max 5 seconds
                    return False, "INVALID_PARAMETER"
            except ValueError:
                return False, "INVALID_PARAMETER"

        # Validate parameters for BUZZ command
        if command == "BUZZ" and parameters[0].upper() not in ["ON", "OFF"]:
            return False, "INVALID_PARAMETER"

        # Validate parameters for TONE command
        if command == "TONE":
            try:
                frequency = int(parameters[0])
                duration_ms = int(parameters[1])
                if frequency < 50 or frequency > 20000:  # Human hearing range
                    return False, "INVALID_PARAMETER"
                if (
                    duration_ms <= 0 or duration_ms > 5000
                ):  # Max 5 seconds (watchdog safe)
                    return False, "INVALID_PARAMETER"
            except ValueError:
                return False, "INVALID_PARAMETER"

        return True, None

    def format_response(self, success, data=None, error=None):
        """
        Format response according to protocol.

        All responses are terminated with newline. Success responses return
        "OK" or data. Error responses return "ERROR:CODE" format.

        Args:
            success (bool): Whether command was successful
            data (str, optional): Response data for successful commands
            error (str, optional): Error code for failed commands

        Returns:
            str: Formatted response with terminator
        """
        if success:
            response = str(data) if data is not None else SUCCESS_RESPONSE
        else:
            if error in ERROR_CODES:
                response = ERROR_CODES[error]
            else:
                response = ERROR_CODES["INVALID_COMMAND"]

        # Ensure response ends with terminator
        if not response.endswith(RESPONSE_TERMINATOR):
            response += RESPONSE_TERMINATOR

        return response

    def format_error_response(self, error_code):
        """
        Format error response.

        Convenience method for formatting error responses.

        Args:
            error_code (str): Error code key from ERROR_CODES

        Returns:
            str: Formatted error response (e.g., "ERROR:INVALID_COMMAND\n")
        """
        return self.format_response(False, error=error_code)

    def format_success_response(self, data=None):
        """
        Format success response.

        Convenience method for formatting successful responses.

        Args:
            data (str, optional): Response data. If None, returns "OK"

        Returns:
            str: Formatted success response with terminator
        """
        return self.format_response(True, data=data)

    def get_relay_status_string(self):
        """
        Get relay status as 8-bit binary string.

        Helper method for STATUS command.

        Returns:
            str: 8-bit binary string where MSB = relay 8, LSB = relay 1.
                 Returns "00000000" if no controller available.
        """
        if not self.relay_controller:
            return "00000000"

        return self.relay_controller.get_status_binary()

    def process_command(self, command_str):
        """
        Process a complete command string.

        Main entry point for command processing. Handles parsing, validation,
        execution, and response formatting. Updates statistics and handles
        all errors gracefully.

        Args:
            command_str (str): Raw command string from serial input

        Returns:
            str: Formatted response string with terminator
        """
        self.command_count += 1
        self.last_command_time = time.ticks_ms()

        if DEBUG_COMMANDS:
            print(f"Processing command #{self.command_count}: '{command_str.strip()}'")

        # Parse command
        command, parameters = self.parse_command(command_str)

        if command is None:
            self.error_count += 1
            return self.format_error_response("INVALID_COMMAND")

        # Validate command
        is_valid, error_message = self.validate_command(command, parameters)
        if not is_valid:
            self.error_count += 1
            return self.format_error_response(error_message)

        # Execute command
        try:
            response = self.execute_command(command, parameters)

            if DEBUG_COMMANDS:
                print(f"Command executed successfully, response: '{response.strip()}'")

            return response

        except Exception as e:
            self.error_count += 1
            if DEBUG:
                print(f"Command execution error: {e}")
            return self.format_error_response("HARDWARE_ERROR")

    def execute_command(self, command, parameters):
        """
        Execute a validated command.

        Dispatches commands to appropriate handlers and formats responses.
        All commands are guaranteed to be valid when this method is called.

        Args:
            command (str): Validated uppercase command name
            parameters (list): Validated parameter list

        Returns:
            str: Formatted response string with terminator

        Note:
            This method assumes validation has already been performed
        """
        if command == "PING":
            return self.format_success_response(
                PING_RESPONSE.replace(RESPONSE_TERMINATOR, "")
            )

        elif command == "STATUS":
            status = self.get_relay_status_string()
            return self.format_success_response(status)

        elif command == "ON":
            relay_num = int(parameters[0])
            if self.relay_controller:
                if self.relay_controller.relay_on(relay_num):
                    return self.format_success_response()
                else:
                    return self.format_error_response("HARDWARE_ERROR")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "OFF":
            relay_num = int(parameters[0])
            if self.relay_controller:
                if self.relay_controller.relay_off(relay_num):
                    return self.format_success_response()
                else:
                    return self.format_error_response("HARDWARE_ERROR")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "ALL":
            operation = parameters[0].upper()
            if self.relay_controller:
                if operation == "ON":
                    if self.relay_controller.all_on():
                        return self.format_success_response()
                    else:
                        return self.format_error_response("HARDWARE_ERROR")
                elif operation == "OFF":
                    if self.relay_controller.all_off():
                        return self.format_success_response()
                    else:
                        return self.format_error_response("HARDWARE_ERROR")
                else:
                    return self.format_error_response("INVALID_PARAMETER")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "SET":
            pattern = parameters[0]
            if self.relay_controller:
                if self.relay_controller.set_pattern(pattern):
                    return self.format_success_response()
                else:
                    return self.format_error_response("HARDWARE_ERROR")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "PULSE":
            relay_num = int(parameters[0])
            duration_ms = int(parameters[1])
            if self.relay_controller:
                # Turn relay on
                if self.relay_controller.relay_on(relay_num):
                    # Schedule turning it off after duration
                    import time

                    time.sleep_ms(duration_ms)
                    self.relay_controller.relay_off(relay_num)
                    return self.format_success_response()
                else:
                    return self.format_error_response("HARDWARE_ERROR")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "INFO":
            # Return board information including UID
            info = get_board_info()
            return self.format_success_response(info)

        elif command == "UID":
            # Return only the unique identifier
            uid = get_board_uid()
            return self.format_success_response(uid)

        elif command == "VERSION":
            # Return firmware version
            return self.format_success_response(FIRMWARE_VERSION)

        elif command == "HELP":
            # Return list of available commands
            help_text = "Commands: PING,STATUS,ON,OFF,ALL,SET,PULSE,INFO,UID,NAME,GET,BEEP,BUZZ,TONE,VERSION,HELP,SAVE,LOAD,CLEAR"
            return self.format_success_response(help_text)

        elif command == "NAME":
            # Set or reset relay name: NAME <relay_number> [<name>]
            relay_num = int(parameters[0])
            if len(parameters) == 1:
                # Clear the name (empty string)
                name = ""
            else:
                # Set custom name
                name = parameters[1]
            if set_relay_name(relay_num, name):
                return self.format_success_response()
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "GET":
            # Get relay name: GET NAME <relay_number>
            if parameters[0].upper() == "NAME":
                relay_num = int(parameters[1])
                name = get_relay_name(relay_num)
                return self.format_success_response(name)
            else:
                return self.format_error_response("INVALID_PARAMETER")

        elif command == "BEEP":
            # Beep: BEEP or BEEP <duration_ms>
            if self.relay_controller:
                duration_ms = 100  # Default beep duration
                if len(parameters) == 1:
                    duration_ms = int(parameters[0])

                if self.relay_controller.buzzer_beep(duration_ms):
                    return self.format_success_response()
                else:
                    return self.format_error_response("HARDWARE_ERROR")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "BUZZ":
            # Buzz: BUZZ ON or BUZZ OFF
            if self.relay_controller:
                operation = parameters[0].upper()
                if operation == "ON":
                    if self.relay_controller.buzzer_on():
                        return self.format_success_response()
                    else:
                        return self.format_error_response("HARDWARE_ERROR")
                elif operation == "OFF":
                    if self.relay_controller.buzzer_off():
                        return self.format_success_response()
                    else:
                        return self.format_error_response("HARDWARE_ERROR")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "TONE":
            # Tone: TONE <frequency_hz> <duration_ms>
            if self.relay_controller:
                frequency = int(parameters[0])
                duration_ms = int(parameters[1])

                if self.relay_controller.buzzer_tone(frequency, duration_ms):
                    return self.format_success_response()
                else:
                    return self.format_error_response("HARDWARE_ERROR")
            else:
                return self.format_error_response("HARDWARE_ERROR")

        elif command == "SAVE":
            # Save current relay states to persistent storage
            # Get states in binary format (MSB = relay 8)
            binary_states = self.relay_controller.get_status_binary()
            # Reverse to storage format (relay 1 first) for consistency
            # MicroPython doesn't support [::-1], so reverse manually
            storage_states = "".join(reversed(binary_states))
            if save_relay_states(storage_states):
                return self.format_success_response("SAVED")
            else:
                return self.format_error_response("SAVE_FAILED")

        elif command == "LOAD":
            # Load saved relay states from persistent storage
            saved_states = load_relay_states()
            if saved_states:
                # Apply the saved states using set_states method
                if self.relay_controller.set_states(saved_states):
                    return self.format_success_response("LOADED")
                else:
                    return self.format_error_response("LOAD_FAILED")
            else:
                return self.format_error_response("NO_SAVED_STATE")

        elif command == "CLEAR":
            # Clear saved relay states from persistent storage
            if clear_relay_states():
                return self.format_success_response("CLEARED")
            else:
                return self.format_error_response("CLEAR_FAILED")

        else:
            return self.format_error_response("INVALID_COMMAND")

    def get_statistics(self):
        """
        Get protocol statistics.

        Useful for monitoring protocol performance and debugging.

        Returns:
            dict: Statistics containing:
                - command_count: Total commands processed
                - error_count: Total errors encountered
                - error_rate: Ratio of errors to commands
                - last_command_time: Ticks timestamp of last command
        """
        return {
            "command_count": self.command_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.command_count, 1),
            "last_command_time": self.last_command_time,
        }

    def get_info(self):
        """
        Get protocol and board information.

        Returns basic board identification without UID.

        Returns:
            str: Info string in format:
                 "WAVESHARE-PICO-RELAY-B,V1.0,8CH,PROTOCOL_1.0"
        """
        return (
            f"{BOARD_NAME},{BOARD_VERSION},{RELAY_COUNT}CH,PROTOCOL_{PROTOCOL_VERSION}"
        )

    def reset_statistics(self):
        """
        Reset command statistics.

        Clears command count, error count, and last command time.
        Useful for starting fresh measurements.
        """
        self.command_count = 0
        self.error_count = 0
        self.last_command_time = 0

        if DEBUG:
            print("Protocol statistics reset")


def test_protocol_parser():
    """
    Test function for protocol parser.

    Runs basic validation tests without hardware. Useful for verifying
    protocol implementation during development.
    """
    print("=== PROTOCOL PARSER TEST ===")

    # Create parser without relay controller for basic testing
    parser = ProtocolParser()

    # Test command parsing
    test_commands = [
        "PING",
        "ping",
        "STATUS",
        "ON 1",
        "OFF 5",
        "on 8",
        "off 3",
        "INVALID",
        "ON",
        "OFF 9",
        "ON abc",
        "",
        "  PING  ",
    ]

    print("Testing command parsing and validation:")
    for cmd in test_commands:
        print(f"\nCommand: '{cmd}'")
        command, params = parser.parse_command(cmd)
        print(f"  Parsed: command='{command}', params={params}")

        if command:
            is_valid, error = parser.validate_command(command, params)
            print(f"  Valid: {is_valid}, Error: {error}")

    # Test response formatting
    print("\nTesting response formatting:")
    responses = [
        parser.format_success_response(),
        parser.format_success_response("PONG"),
        parser.format_success_response("10101010"),
        parser.format_error_response("INVALID_COMMAND"),
        parser.format_error_response("INVALID_RELAY_NUMBER"),
    ]

    for resp in responses:
        print(f"  Response: '{resp.strip()}'")

    # Test command processing (without relay controller)
    print("\nTesting command processing (no relay controller):")
    test_cmds = ["PING", "STATUS", "ON 1", "INVALID"]
    for cmd in test_cmds:
        response = parser.process_command(cmd)
        print(f"  '{cmd}' -> '{response.strip()}'")

    # Show statistics
    print("\nProtocol Statistics:")
    stats = parser.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nProtocol parser test complete!")


if __name__ == "__main__":
    test_protocol_parser()
