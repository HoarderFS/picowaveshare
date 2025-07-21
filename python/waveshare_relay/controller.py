"""
Main controller class for Waveshare Pico Relay B board.

Provides complete control interface for the 8-channel relay board including
individual relay control, bulk operations, state persistence, buzzer control,
and device management through ASCII serial protocol communication.
"""

import time

import serial

from .exceptions import (
    RelayCommandError,
    RelayConnectionError,
    RelayTimeoutError,
)
from .protocol import RelayProtocol

# Configuration constants
DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 1.0
CONNECTION_TIMEOUT = 5.0
CONNECTION_POLL_DELAY = 0.1


class RelayController:
    """
    Main controller class for the Waveshare Pico Relay B board.

    Provides high-level interface for controlling relays, buzzer, and
    state persistence via serial communication using the ASCII protocol.

    Features:
    - Individual relay control (on/off)
    - Bulk relay operations (all on/off, pattern setting)
    - Relay pulse operations with timing
    - Buzzer control (beep, continuous, tones)
    - State persistence (save/load/clear)
    - Relay naming for identification
    - Board information queries (version, UID, help)
    - Automatic device discovery
    - Context manager support for automatic cleanup
    """

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize relay controller

        Args:
            port: Serial port path (e.g., '/dev/cu.usbmodem84401')
            baudrate: Serial communication baud rate (default: 115200)
            timeout: Command timeout in seconds (default: 1.0)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.protocol = RelayProtocol()
        self.connected = False

    def connect(self) -> None:
        """
        Connect to the relay board

        Raises:
            RelayConnectionError: If connection fails
        """
        try:
            self.serial = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )

            # Set connected temporarily for ping test
            self.connected = True

            # Poll for connection readiness with timeout
            start_time = time.time()

            while time.time() - start_time < CONNECTION_TIMEOUT:
                if self.ping():
                    return  # Connection successful
                # Small delay between polling attempts
                time.sleep(CONNECTION_POLL_DELAY)

            # If we get here, connection failed
            self.connected = False
            raise RelayConnectionError("Board not responding to PING after timeout")

        except serial.SerialException as e:
            raise RelayConnectionError(f"Failed to connect to {self.port}: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from the relay board"""
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def _send_command(self, command: str, *args) -> str:
        """
        Send a command to the relay board and return response

        Args:
            command: Command name
            *args: Command parameters

        Returns:
            Response data string

        Raises:
            RelayConnectionError: If not connected
            RelayTimeoutError: If command times out
            RelayCommandError: If board returns error
            RelayValidationError: If command parameters are invalid
        """
        if not self.connected or not self.serial:
            raise RelayConnectionError("Not connected to relay board")

        # Encode command
        cmd_string = self.protocol.encode_command(command, *args)

        # Send command
        try:
            self.serial.write(cmd_string.encode("utf-8"))
            self.serial.flush()

            # Read response
            response_bytes = self.serial.readline()
            if not response_bytes:
                raise RelayTimeoutError(f"Timeout waiting for response to {command}")

            response = response_bytes.decode("utf-8").strip()

        except serial.SerialException as e:
            raise RelayConnectionError(f"Serial communication error: {e}") from e

        # Decode response
        is_success, data, error_code = self.protocol.decode_response(response)

        if not is_success:
            raise RelayCommandError(
                f"Command {command} failed: {error_code}", error_code
            )

        return data

    def ping(self) -> bool:
        """
        Test connection to relay board

        Returns:
            True if board responds, False otherwise
        """
        try:
            response = self._send_command("PING")
            return response == "PONG"
        except Exception:
            return False

    def get_info(self) -> dict[str, str]:
        """
        Get board information

        Returns:
            Dictionary with board information
        """
        response = self._send_command("INFO")
        return self.protocol.parse_info_response(response)

    def get_uid(self) -> str:
        """
        Get board unique identifier

        Returns:
            16-character hex string
        """
        return self._send_command("UID")

    def get_status(self) -> dict[int, bool]:
        """
        Get status of all relays

        Returns:
            Dictionary mapping relay numbers (1-8) to boolean states
        """
        response = self._send_command("STATUS")
        return self.protocol.parse_status_response(response)

    def relay_on(self, relay_num: int) -> None:
        """
        Turn on a specific relay

        Args:
            relay_num: Relay number (1-8)
        """
        self._send_command("ON", relay_num)

    def relay_off(self, relay_num: int) -> None:
        """
        Turn off a specific relay

        Args:
            relay_num: Relay number (1-8)
        """
        self._send_command("OFF", relay_num)

    def all_relays_on(self) -> None:
        """Turn all relays on"""
        self._send_command("ALL", "ON")

    def all_relays_off(self) -> None:
        """Turn all relays off"""
        self._send_command("ALL", "OFF")

    def set_relay_pattern(self, pattern: str) -> None:
        """
        Set relay states using 8-bit binary pattern

        Args:
            pattern: 8-bit binary string (MSB=relay8, LSB=relay1)
        """
        self._send_command("SET", pattern)

    def pulse_relay(self, relay_num: int, duration_ms: int) -> None:
        """
        Pulse a relay (turn on for duration then off)

        Args:
            relay_num: Relay number (1-8)
            duration_ms: Duration in milliseconds (1-5000)
        """
        self._send_command("PULSE", relay_num, duration_ms)

    def set_relay_name(self, relay_num: int, name: str) -> None:
        """
        Set persistent name for a relay

        Args:
            relay_num: Relay number (1-8)
            name: Name string (1-32 characters)
        """
        self._send_command("NAME", relay_num, name)

    def get_relay_name(self, relay_num: int) -> str:
        """
        Get name of a specific relay

        Args:
            relay_num: Relay number (1-8)

        Returns:
            Relay name string
        """
        return self._send_command("GET", "NAME", relay_num)

    def beep(self, duration_ms: int | None = None) -> None:
        """
        Produce a short beep

        Args:
            duration_ms: Optional duration in milliseconds (1-5000)
        """
        if duration_ms is None:
            self._send_command("BEEP")
        else:
            self._send_command("BEEP", duration_ms)

    def buzzer_on(self) -> None:
        """Turn buzzer on continuously"""
        self._send_command("BUZZ", "ON")

    def buzzer_off(self) -> None:
        """Turn buzzer off"""
        self._send_command("BUZZ", "OFF")

    def tone(self, frequency: int, duration_ms: int) -> None:
        """
        Play a tone at specific frequency and duration

        Args:
            frequency: Frequency in Hz (50-20000)
            duration_ms: Duration in milliseconds (1-5000)
        """
        self._send_command("TONE", frequency, duration_ms)

    def get_relay_states_dict(self) -> dict[int, dict[str, bool | str]]:
        """
        Get comprehensive relay information including names and states

        Returns:
            Dictionary with relay info including names and states
        """
        states = self.get_status()
        result = {}

        for relay_num in range(1, 9):
            try:
                name = self.get_relay_name(relay_num)
            except Exception:
                name = f"Relay {relay_num}"

            result[relay_num] = {
                "name": name,
                "state": states[relay_num],
                "state_str": "ON" if states[relay_num] else "OFF",
            }

        return result

    def get_version(self) -> str:
        """
        Get firmware version from the board.

        Returns:
            str: Version string (e.g., "1.1.0")
        """
        return self._send_command("VERSION")

    def get_help(self) -> list[str]:
        """
        Get list of available commands from the board.

        Returns:
            list[str]: List of available command names
        """
        response = self._send_command("HELP")
        # Response format: "Commands: PING,STATUS,ON,OFF,..."
        if response.startswith("Commands: "):
            command_str = response[10:]  # Remove "Commands: " prefix
            return command_str.split(",")
        return []

    def save_state(self) -> None:
        """
        Save current relay states to persistent storage.

        The saved states will be restored automatically on board boot
        if auto-load is enabled (default).

        Raises:
            RelayCommandError: If save operation fails
        """
        response = self._send_command("SAVE")
        if response != "SAVED":
            raise RelayCommandError(f"Unexpected save response: {response}")

    def load_state(self) -> None:
        """
        Load previously saved relay states from persistent storage.

        Applies the saved relay configuration to all relays.

        Raises:
            RelayCommandError: If no saved states exist or load fails
        """
        response = self._send_command("LOAD")
        if response != "LOADED":
            raise RelayCommandError(f"Unexpected load response: {response}")

    def clear_state(self) -> None:
        """
        Clear saved relay states from persistent storage.

        After calling this, load_state() will fail until save_state() is called again.
        This operation cannot be undone.

        Raises:
            RelayCommandError: If clear operation fails
        """
        response = self._send_command("CLEAR")
        if response != "CLEARED":
            raise RelayCommandError(f"Unexpected clear response: {response}")
