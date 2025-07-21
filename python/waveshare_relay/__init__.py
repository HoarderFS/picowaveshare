"""
Waveshare Pico Relay B - Python Library

A comprehensive Python library for controlling the Waveshare Pico Relay B board
via USB serial communication using an ASCII protocol.

Features:
- Individual and bulk relay control
- State persistence across power cycles
- Buzzer control (beep, tone, continuous)
- Relay naming for identification
- Automatic device discovery
- Board information queries (UID, version, help)
- Context manager support
- Comprehensive error handling

Classes:
    RelayController: Main controller class for relay board communication
    RelayProtocol: Protocol encoder/decoder for command formatting
    RelayError: Base exception class for relay-related errors

Functions:
    discover_relay_boards: Find all connected relay boards
    find_relay_board: Find the first available relay board

Examples:
    Basic usage:
    >>> from waveshare_relay import RelayController, find_relay_board
    >>> port = find_relay_board()
    >>> with RelayController(port) as controller:
    ...     controller.relay_on(1)
    ...     controller.save_state()  # Persist across power cycles

    Advanced features:
    >>> controller.set_relay_name(1, "LIGHTS")
    >>> controller.tone(440, 1000)  # A4 note for 1 second
    >>> print(f"Firmware: {controller.get_version()}")
"""

__version__ = "0.1.0"
__author__ = "Waveshare Pico Relay B Project"
__license__ = "MIT"

from .controller import RelayController
from .discovery import discover_relay_boards, find_relay_board
from .exceptions import (
    RelayCommandError,
    RelayConnectionError,
    RelayError,
    RelayTimeoutError,
)
from .protocol import RelayProtocol

__all__ = [
    "RelayController",
    "RelayProtocol",
    "RelayError",
    "RelayConnectionError",
    "RelayTimeoutError",
    "RelayCommandError",
    "discover_relay_boards",
    "find_relay_board",
]
