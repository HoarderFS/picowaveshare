"""
USB device discovery module for Waveshare Pico Relay B Controller.

Provides automatic discovery of connected relay boards using protocol-based
detection. This module can identify boards by testing the protocol response
to PING commands, making it more reliable than USB descriptor matching.
"""

import logging

import serial.tools.list_ports

logger = logging.getLogger(__name__)

# Configuration constants
DISCOVERY_TIMEOUT = 2.0


class RelayBoardDiscovery:
    """
    Discovers Waveshare Pico Relay B Controller boards via USB descriptors
    """

    # USB identifiers for our board
    EXPECTED_MANUFACTURER = "Waveshare"
    EXPECTED_PRODUCT = "Pico Relay B Controller"
    EXPECTED_VENDOR_ID = "2e8a"  # Raspberry Pi Foundation
    EXPECTED_PRODUCT_ID = "0005"  # MicroPython board

    @classmethod
    def discover_boards(cls) -> list[dict[str, str]]:
        """
        Discover all connected Waveshare Pico Relay B Controller boards

        Returns:
            List of board info dictionaries with keys:
            - port: serial port path
            - serial_number: board serial number
            - manufacturer: USB manufacturer string
            - product: USB product string
        """
        boards = []

        # Use protocol-based discovery (most reliable method)
        try:
            boards.extend(cls._discover_boards())
        except Exception as e:
            logger.debug(f"Discovery failed: {e}")

        return boards

    @classmethod
    def find_first_board(cls) -> str | None:
        """
        Find the first available Waveshare Pico Relay B Controller

        Returns:
            Serial port path or None if no board found
        """
        boards = cls.discover_boards()
        return boards[0]["port"] if boards else None

    @classmethod
    def _discover_boards(cls) -> list[dict[str, str]]:
        """Discover boards by scanning serial ports and testing protocol"""
        boards = []

        try:
            # Get all available serial ports (cross-platform)
            ports = serial.tools.list_ports.comports()

            for port_info in ports:
                port = port_info.device
                logger.debug(
                    f"Checking port: {port} - {port_info.description} [{port_info.hwid}]"
                )

                # Quick filter: Check if this might be a Pico board
                if port_info.vid == 0x2E8A:  # Raspberry Pi Foundation
                    logger.debug(f"Found Raspberry Pi device at {port}")

                try:
                    # Try to connect and identify the device
                    from .controller import RelayController

                    controller = RelayController(port, timeout=DISCOVERY_TIMEOUT)
                    controller.connect()

                    # Try to get device info
                    try:
                        info = controller.get_info()
                        uid = controller.get_uid()

                        # Check if this looks like our board
                        board_name = info.get("board_name", "").upper()
                        if "PICO" in board_name and "RELAY" in board_name:
                            boards.append(
                                {
                                    "port": port,
                                    "serial_number": f"RELAY-{uid[:8]}",
                                    "manufacturer": "Waveshare",
                                    "product": "Pico Relay B Controller",
                                }
                            )
                    except Exception:
                        # Device doesn't respond to our protocol
                        pass

                    controller.disconnect()

                except Exception:
                    # Failed to connect or communicate
                    continue

        except Exception as e:
            logger.debug(f"Port scan error: {e}")

        return boards


def discover_relay_boards() -> list[dict[str, str]]:
    """
    Convenience function to discover all Waveshare Pico Relay B Controller boards

    Returns:
        List of board info dictionaries
    """
    return RelayBoardDiscovery.discover_boards()


def find_relay_board() -> str | None:
    """
    Convenience function to find the first available Waveshare Pico Relay B Controller

    Returns:
        Serial port path or None if no board found
    """
    return RelayBoardDiscovery.find_first_board()
