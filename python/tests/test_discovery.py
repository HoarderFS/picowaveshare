"""
Tests for the USB device discovery module
"""

import os
from unittest.mock import Mock, patch

import pytest
from waveshare_relay.discovery import (
    RelayBoardDiscovery,
    discover_relay_boards,
    find_relay_board,
)


class TestRelayBoardDiscovery:
    """Test cases for RelayBoardDiscovery class"""

    def _is_hardware_test(self):
        """Check if running hardware tests"""
        return os.environ.get("HARDWARE_TEST", "false").lower() == "true"

    @patch("waveshare_relay.discovery.serial.tools.list_ports.comports")
    def test_discover_boards_no_ports(self, mock_comports):
        """Test discovery when no serial ports are available"""
        if self._is_hardware_test():
            pytest.skip("Mock test not applicable for hardware testing")

        mock_comports.return_value = []
        boards = RelayBoardDiscovery.discover_boards()
        assert boards == []

    @patch("waveshare_relay.discovery.serial.tools.list_ports.comports")
    @patch("waveshare_relay.controller.RelayController")
    def test_discover_boards_with_relay_board(
        self, mock_controller_class, mock_comports
    ):
        """Test discovery when a relay board is found"""
        if self._is_hardware_test():
            pytest.skip("Mock test not applicable for hardware testing")

        # Mock port info
        mock_port = Mock()
        mock_port.device = "/dev/cu.usbmodem123"
        mock_port.description = "USB Serial"
        mock_port.hwid = "USB VID:PID=2E8A:0005"
        mock_port.vid = 0x2E8A
        mock_port.pid = 0x0005

        mock_comports.return_value = [mock_port]

        # Mock controller
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.connect = Mock()
        mock_controller.disconnect = Mock()
        mock_controller.get_info = Mock(
            return_value={
                "board_name": "WAVESHARE-PICO-RELAY-B",
                "version": "V1.0",
                "channels": "8CH",
                "uid": "ABC12345",
            }
        )
        mock_controller.get_uid = Mock(return_value="ABC12345")

        boards = RelayBoardDiscovery.discover_boards()

        assert len(boards) == 1
        assert boards[0]["port"] == "/dev/cu.usbmodem123"
        assert boards[0]["serial_number"] == "RELAY-ABC12345"
        assert boards[0]["manufacturer"] == "Waveshare"
        assert boards[0]["product"] == "Pico Relay B Controller"

    @patch("waveshare_relay.discovery.serial.tools.list_ports.comports")
    @patch("waveshare_relay.controller.RelayController")
    def test_discover_boards_non_relay_device(
        self, mock_controller_class, mock_comports
    ):
        """Test discovery when device doesn't respond to relay protocol"""
        if self._is_hardware_test():
            pytest.skip("Mock test not applicable for hardware testing")

        # Mock port info
        mock_port = Mock()
        mock_port.device = "/dev/cu.usbmodem123"
        mock_port.description = "USB Serial"
        mock_port.hwid = "USB VID:PID=1234:5678"
        mock_port.vid = 0x1234

        mock_comports.return_value = [mock_port]

        # Mock controller that fails to connect
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.connect.side_effect = Exception("Connection failed")

        boards = RelayBoardDiscovery.discover_boards()
        assert boards == []

    def test_discover_boards_hardware(self):
        """Test discovery with real hardware"""
        if not self._is_hardware_test():
            pytest.skip("Hardware test only runs with HARDWARE_TEST=true")

        boards = discover_relay_boards()

        # Should find at least one board when hardware is connected
        assert len(boards) > 0

        # Verify board info structure
        board = boards[0]
        assert "port" in board
        assert "serial_number" in board
        assert "manufacturer" in board
        assert "product" in board

        # Verify expected values
        assert board["manufacturer"] == "Waveshare"
        assert board["product"] == "Pico Relay B Controller"
        assert board["serial_number"].startswith("RELAY-")

    def test_find_relay_board_hardware(self):
        """Test find_relay_board with real hardware"""
        if not self._is_hardware_test():
            pytest.skip("Hardware test only runs with HARDWARE_TEST=true")

        port = find_relay_board()

        # Should find a port when hardware is connected
        assert port is not None
        assert port.startswith("/dev/")

    @patch("waveshare_relay.discovery.serial.tools.list_ports.comports")
    def test_find_relay_board_no_boards(self, mock_comports):
        """Test find_relay_board when no boards are found"""
        if self._is_hardware_test():
            pytest.skip("Mock test not applicable for hardware testing")

        mock_comports.return_value = []
        port = find_relay_board()
        assert port is None

    def test_raspberry_pi_vid_filter(self):
        """Test that Raspberry Pi VID is correctly identified"""
        assert RelayBoardDiscovery.EXPECTED_VENDOR_ID == "2e8a"
        assert RelayBoardDiscovery.EXPECTED_PRODUCT_ID == "0005"
