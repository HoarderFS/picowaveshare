"""
Tests for the RelayController class
"""

import os
from unittest.mock import Mock, patch

import pytest
import serial
from waveshare_relay.controller import RelayController
from waveshare_relay.exceptions import (
    RelayCommandError,
    RelayConnectionError,
    RelayTimeoutError,
)


class TestRelayController:
    """Test cases for RelayController class"""

    def _is_hardware_test(self):
        """Check if running hardware tests"""
        return os.environ.get("HARDWARE_TEST", "false").lower() == "true"

    def test_init(self):
        """Test RelayController initialization"""
        controller = RelayController("/dev/test", baudrate=9600, timeout=2.0)

        assert controller.port == "/dev/test"
        assert controller.baudrate == 9600
        assert controller.timeout == 2.0
        assert controller.serial is None
        assert controller.connected is False
        assert controller.protocol is not None

    def test_init_defaults(self):
        """Test RelayController initialization with defaults"""
        controller = RelayController("/dev/test")

        assert controller.port == "/dev/test"
        assert controller.baudrate == 115200
        assert controller.timeout == 1.0

    @patch("waveshare_relay.controller.serial.Serial")
    def test_connect_success(self, mock_serial_class):
        """Test successful connection"""
        # Mock serial instance
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        controller = RelayController("/dev/test")

        # Mock successful ping
        with patch.object(controller, "ping", return_value=True):
            controller.connect()

        # Verify connection
        assert controller.connected is True
        assert controller.serial == mock_serial
        mock_serial_class.assert_called_once_with(
            port="/dev/test", baudrate=115200, timeout=1.0
        )

    @patch("waveshare_relay.controller.serial.Serial")
    def test_connect_ping_timeout(self, mock_serial_class):
        """Test connection timeout when ping fails"""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        controller = RelayController("/dev/test")

        # Mock failed ping
        with (
            patch.object(controller, "ping", return_value=False),
            patch("time.time", side_effect=[0, 6]),  # Simulate timeout
            pytest.raises(
                RelayConnectionError,
                match="Board not responding to PING after timeout",
            ),
        ):
            controller.connect()

        assert controller.connected is False

    @patch("waveshare_relay.controller.serial.Serial")
    def test_connect_serial_exception(self, mock_serial_class):
        """Test connection with serial exception"""
        mock_serial_class.side_effect = serial.SerialException("Port not found")

        controller = RelayController("/dev/test")

        with pytest.raises(
            RelayConnectionError, match="Failed to connect to /dev/test"
        ):
            controller.connect()

    def test_disconnect(self):
        """Test disconnection"""
        controller = RelayController("/dev/test")
        mock_serial = Mock()
        mock_serial.is_open = True
        controller.serial = mock_serial
        controller.connected = True

        controller.disconnect()

        assert controller.connected is False
        mock_serial.close.assert_called_once()

    def test_disconnect_no_serial(self):
        """Test disconnection with no serial connection"""
        controller = RelayController("/dev/test")
        controller.connected = True

        # Should not raise exception
        controller.disconnect()
        assert controller.connected is False

    def test_context_manager(self):
        """Test context manager functionality"""
        controller = RelayController("/dev/test")

        with (
            patch.object(controller, "connect") as mock_connect,
            patch.object(controller, "disconnect") as mock_disconnect,
            controller,
        ):
            pass

        mock_connect.assert_called_once()
        mock_disconnect.assert_called_once()

    def test_send_command_not_connected(self, controller):
        """Test sending command when not connected"""
        with pytest.raises(RelayConnectionError, match="Not connected to relay board"):
            controller._send_command("PING")

    def test_send_command_success(self, connected_controller, mock_serial):
        """Test successful command sending"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware
            result = connected_controller._send_command("PING")
            assert result == "PONG"
        else:
            # Mock successful response
            mock_serial.readline.return_value = b"PONG\r\n"

            result = connected_controller._send_command("PING")

            assert result == "PONG"
            mock_serial.write.assert_called_once_with(b"PING\n")
            mock_serial.flush.assert_called_once()
            mock_serial.readline.assert_called_once()

    def test_send_command_timeout(self, connected_controller, mock_serial):
        """Test command timeout"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Skip timeout test with real hardware - would take too long
            pytest.skip("Timeout test not applicable for hardware testing")
        else:
            # Mock timeout (empty response)
            mock_serial.readline.return_value = b""

            with pytest.raises(
                RelayTimeoutError, match="Timeout waiting for response to PING"
            ):
                connected_controller._send_command("PING")

    def test_send_command_error_response(self, connected_controller, mock_serial):
        """Test command with error response"""
        if self._is_hardware_test():
            # Skip error response test with real hardware - error handling is tested elsewhere
            pytest.skip("Error response test not applicable for hardware testing")
        else:
            # Mock error response
            mock_serial.readline.return_value = b"ERROR:INVALID_COMMAND\r\n"

            with pytest.raises(
                RelayCommandError, match="Command PING failed: INVALID_COMMAND"
            ):
                connected_controller._send_command("PING")

    def test_send_command_serial_exception(self, connected_controller, mock_serial):
        """Test command with serial exception"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Skip serial exception test with real hardware
            pytest.skip("Serial exception test not applicable for hardware testing")
        else:
            mock_serial.write.side_effect = serial.SerialException("Connection lost")

            with pytest.raises(
                RelayConnectionError, match="Serial communication error"
            ):
                connected_controller._send_command("PING")

    def test_ping_success(self, connected_controller, mock_serial):
        """Test successful ping"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware
            result = connected_controller.ping()
            assert result is True
        else:
            mock_serial.readline.return_value = b"PONG\r\n"

            result = connected_controller.ping()
            assert result is True

    def test_ping_failure(self, connected_controller, mock_serial):
        """Test ping failure"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Skip ping failure test with real hardware - ping should always work
            pytest.skip("Ping failure test not applicable for hardware testing")
        else:
            mock_serial.readline.return_value = b"ERROR:INVALID_COMMAND\r\n"

            result = connected_controller.ping()
            assert result is False

    def test_get_info(self, connected_controller, mock_serial):
        """Test get_info command"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware
            info = connected_controller.get_info()
            # Just verify we get a valid info dict with required keys
            assert isinstance(info, dict)
            assert "board_name" in info
            # Don't check exact values as they may vary by hardware
        else:
            mock_serial.readline.return_value = (
                b"WAVESHARE-PICO-RELAY-B,V1.0,8CH,UID:1234\r\n"
            )

            info = connected_controller.get_info()

            expected = {
                "board_name": "WAVESHARE-PICO-RELAY-B",
                "version": "V1.0",
                "channels": "8CH",
                "uid": "1234",
            }
            assert info == expected

    def test_get_uid(self, connected_controller, mock_serial):
        """Test get_uid command"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware
            uid = connected_controller.get_uid()
            # Just verify we get a non-empty UID string
            assert isinstance(uid, str)
            assert len(uid) > 0
        else:
            mock_serial.readline.return_value = b"ECD43B7502A23159\r\n"

            uid = connected_controller.get_uid()
            assert uid == "ECD43B7502A23159"

    def test_get_status(self, connected_controller, mock_serial):
        """Test get_status command"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware
            status = connected_controller.get_status()
            # Just verify we get a valid status dict
            assert isinstance(status, dict)
            assert len(status) == 8
            for i in range(1, 9):
                assert i in status
                assert isinstance(status[i], bool)
        else:
            mock_serial.readline.return_value = b"10101010\r\n"

            status = connected_controller.get_status()

            expected = {
                1: False,
                2: True,
                3: False,
                4: True,
                5: False,
                6: True,
                7: False,
                8: True,
            }
            assert status == expected

    def test_relay_on(self, connected_controller, mock_serial):
        """Test relay_on command"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware - verify relay actually turns on
            import time

            connected_controller.relay_off(1)  # Start with relay off
            time.sleep(0.1)
            connected_controller.relay_on(1)
            time.sleep(0.1)
            status = connected_controller.get_status()
            assert status[1] is True
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.relay_on(1)
            mock_serial.write.assert_called_with(b"ON 1\n")

    def test_relay_off(self, connected_controller, mock_serial):
        """Test relay_off command"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware - verify relay actually turns off
            import time

            connected_controller.relay_on(3)  # Start with relay on
            time.sleep(0.1)
            connected_controller.relay_off(3)
            time.sleep(0.1)
            status = connected_controller.get_status()
            assert status[3] is False
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.relay_off(3)
            mock_serial.write.assert_called_with(b"OFF 3\n")

    def test_all_relays_on(self, connected_controller, mock_serial):
        """Test all_relays_on command"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware - verify all relays turn on
            import time

            connected_controller.all_relays_on()
            time.sleep(0.1)
            status = connected_controller.get_status()
            assert all(status.values())
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.all_relays_on()
            mock_serial.write.assert_called_with(b"ALL ON\n")

    def test_all_relays_off(self, connected_controller, mock_serial):
        """Test all_relays_off command"""
        if os.environ.get("HARDWARE_TEST", "false").lower() == "true":
            # Test with real hardware - verify all relays turn off
            import time

            connected_controller.all_relays_off()
            time.sleep(0.1)
            status = connected_controller.get_status()
            assert all(not state for state in status.values())
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.all_relays_off()
            mock_serial.write.assert_called_with(b"ALL OFF\n")

    def test_set_relay_pattern(self, connected_controller, mock_serial):
        """Test set_relay_pattern command"""
        if self._is_hardware_test():
            # Test with real hardware - verify pattern is actually set
            import time

            connected_controller.set_relay_pattern("10101010")
            time.sleep(0.1)
            status = connected_controller.get_status()
            expected = [False, True, False, True, False, True, False, True]
            actual = [status[i + 1] for i in range(8)]
            assert actual == expected
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.set_relay_pattern("10101010")
            mock_serial.write.assert_called_with(b"SET 10101010\n")

    def test_pulse_relay(self, connected_controller, mock_serial):
        """Test pulse_relay command"""
        if self._is_hardware_test():
            # Test with real hardware - just verify command executes without error
            connected_controller.pulse_relay(1, 200)
            # Don't test timing as it's complex in a test environment
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.pulse_relay(1, 500)
            mock_serial.write.assert_called_with(b"PULSE 1 500\n")

    def test_set_relay_name(self, connected_controller, mock_serial):
        """Test set_relay_name command"""
        if self._is_hardware_test():
            # Test with real hardware
            connected_controller.set_relay_name(1, "TEST_LIGHT")
            # Just verify command executes without error
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.set_relay_name(1, "LIGHTS")
            mock_serial.write.assert_called_with(b"NAME 1 LIGHTS\n")
            
    def test_reset_relay_name(self, connected_controller, mock_serial):
        """Test resetting relay name to empty string"""
        if self._is_hardware_test():
            # Test with real hardware
            connected_controller.set_relay_name(1)  # Clear the name
            name = connected_controller.get_relay_name(1)
            assert name == ""
        else:
            mock_serial.readline.side_effect = [b"OK\r\n", b"\r\n"]
            connected_controller.set_relay_name(1)  # Clear the name
            mock_serial.write.assert_called_with(b"NAME 1\n")
            # Verify name was cleared
            name = connected_controller.get_relay_name(1)
            assert name == ""

    def test_get_relay_name(self, connected_controller, mock_serial):
        """Test get_relay_name command"""
        if self._is_hardware_test():
            # Test with real hardware
            name = connected_controller.get_relay_name(1)
            assert isinstance(name, str)
            assert len(name) > 0
        else:
            mock_serial.readline.return_value = b"LIGHTS\r\n"
            name = connected_controller.get_relay_name(1)
            assert name == "LIGHTS"
            mock_serial.write.assert_called_with(b"GET NAME 1\n")

    def test_beep_default(self, connected_controller, mock_serial):
        """Test beep command with default duration"""
        if self._is_hardware_test():
            # Test with real hardware - just verify command executes
            connected_controller.beep()
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.beep()
            mock_serial.write.assert_called_with(b"BEEP\n")

    def test_beep_with_duration(self, connected_controller, mock_serial):
        """Test beep command with custom duration"""
        if self._is_hardware_test():
            # Test with real hardware - just verify command executes
            connected_controller.beep(500)
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.beep(500)
            mock_serial.write.assert_called_with(b"BEEP 500\n")

    def test_buzzer_on(self, connected_controller, mock_serial):
        """Test buzzer_on command"""
        if self._is_hardware_test():
            # Test with real hardware - just verify command executes
            connected_controller.buzzer_on()
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.buzzer_on()
            mock_serial.write.assert_called_with(b"BUZZ ON\n")

    def test_buzzer_off(self, connected_controller, mock_serial):
        """Test buzzer_off command"""
        if self._is_hardware_test():
            # Test with real hardware - just verify command executes
            connected_controller.buzzer_off()
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.buzzer_off()
            mock_serial.write.assert_called_with(b"BUZZ OFF\n")

    def test_tone(self, connected_controller, mock_serial):
        """Test tone command"""
        if self._is_hardware_test():
            # Test with real hardware - just verify command executes
            connected_controller.tone(1000, 500)
        else:
            mock_serial.readline.return_value = b"OK\r\n"
            connected_controller.tone(1000, 500)
            mock_serial.write.assert_called_with(b"TONE 1000 500\n")

    def test_get_relay_states_dict(self, connected_controller, mock_serial):
        """Test get_relay_states_dict command"""
        if self._is_hardware_test():
            # Test with real hardware - just verify structure is correct
            result = connected_controller.get_relay_states_dict()
            assert isinstance(result, dict)
            assert len(result) == 8
            for i in range(1, 9):
                assert i in result
                assert "name" in result[i]
                assert "state" in result[i]
                assert "state_str" in result[i]
        else:
            # Mock status response
            mock_serial.readline.side_effect = [
                b"10101010\r\n",  # STATUS response
                b"LIGHT1\r\n",  # GET NAME 1 response
                b"LIGHT2\r\n",  # GET NAME 2 response
                b"\r\n",  # GET NAME 3 response (default empty)
                b"\r\n",  # GET NAME 4 response
                b"\r\n",  # GET NAME 5 response
                b"\r\n",  # GET NAME 6 response
                b"\r\n",  # GET NAME 7 response
                b"\r\n",  # GET NAME 8 response
            ]

            result = connected_controller.get_relay_states_dict()

            expected = {
                1: {"name": "LIGHT1", "state": False, "state_str": "OFF"},
                2: {"name": "LIGHT2", "state": True, "state_str": "ON"},
                3: {"name": "", "state": False, "state_str": "OFF"},
                4: {"name": "", "state": True, "state_str": "ON"},
                5: {"name": "", "state": False, "state_str": "OFF"},
                6: {"name": "", "state": True, "state_str": "ON"},
                7: {"name": "", "state": False, "state_str": "OFF"},
                8: {"name": "", "state": True, "state_str": "ON"},
            }
            assert result == expected

    def test_get_relay_states_dict_name_error(self, connected_controller, mock_serial):
        """Test get_relay_states_dict with name retrieval error"""
        if self._is_hardware_test():
            # Skip error testing with real hardware
            pytest.skip("Error condition test not applicable for hardware testing")
        else:
            # Mock status response and error for name
            mock_serial.readline.side_effect = [
                b"00000000\r\n",  # STATUS response
                b"ERROR:INVALID_COMMAND\r\n",  # GET NAME 1 error
                b"\r\n",  # GET NAME 2 response
                b"\r\n",  # GET NAME 3 response
                b"\r\n",  # GET NAME 4 response
                b"\r\n",  # GET NAME 5 response
                b"\r\n",  # GET NAME 6 response
                b"\r\n",  # GET NAME 7 response
                b"\r\n",  # GET NAME 8 response
            ]

            result = connected_controller.get_relay_states_dict()

            # Should use empty string when error occurs
            assert result[1]["name"] == ""
            assert result[2]["name"] == ""
