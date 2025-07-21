"""
Pytest configuration and fixtures for waveshare_relay tests
"""

import os
from unittest.mock import Mock

import pytest
from waveshare_relay import RelayController, find_relay_board

# Hardware testing configuration
HARDWARE_TEST = os.environ.get("HARDWARE_TEST", "false").lower() == "true"


def find_hardware_port():
    """Find connected Pico board for hardware testing using auto-discovery"""
    if not HARDWARE_TEST:
        return None

    # First check if a port is specified in environment
    env_port = os.environ.get("RELAY_PORT")
    if env_port:
        return env_port

    # Otherwise use auto-discovery
    port = find_relay_board()
    if not port:
        print("WARNING: No relay board found via auto-discovery")
        print("You can specify a port using: export RELAY_PORT=/dev/cu.usbmodem...")
    return port


@pytest.fixture
def mock_serial():
    """Mock serial.Serial object for testing"""
    mock = Mock()
    mock.is_open = True
    mock.write = Mock()
    mock.flush = Mock()
    mock.readline = Mock()
    mock.close = Mock()
    return mock


@pytest.fixture
def controller():
    """Create a RelayController instance for testing"""
    if HARDWARE_TEST:
        port = find_hardware_port()
        if port:
            return RelayController(port, baudrate=115200, timeout=2.0)
        else:
            pytest.skip("No hardware found for hardware testing")
    return RelayController("/dev/test", baudrate=115200, timeout=1.0)


@pytest.fixture
def connected_controller(controller, mock_serial):
    """Create a connected RelayController (mocked or real hardware)"""
    if HARDWARE_TEST:
        # Use real hardware connection
        controller.connect()
        # Ensure all relays start OFF for consistent testing
        controller.all_relays_off()
        yield controller
        # Cleanup - turn off all relays
        controller.all_relays_off()
        controller.disconnect()
    else:
        # Use mocked connection
        controller.serial = mock_serial
        controller.connected = True
        yield controller
