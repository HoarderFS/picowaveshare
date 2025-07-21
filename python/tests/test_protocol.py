"""
Tests for the RelayProtocol class
"""

import pytest
from waveshare_relay.exceptions import RelayValidationError
from waveshare_relay.protocol import RelayProtocol


class TestRelayProtocol:
    """Test cases for RelayProtocol class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.protocol = RelayProtocol()

    def test_validate_relay_number(self):
        """Test relay number validation"""
        # Valid relay numbers
        assert self.protocol.validate_relay_number(1) is True
        assert self.protocol.validate_relay_number(8) is True
        assert self.protocol.validate_relay_number(5) is True

        # Invalid relay numbers
        assert self.protocol.validate_relay_number(0) is False
        assert self.protocol.validate_relay_number(9) is False
        assert self.protocol.validate_relay_number(-1) is False
        assert self.protocol.validate_relay_number("1") is False
        assert self.protocol.validate_relay_number(1.5) is False

    def test_validate_binary_pattern(self):
        """Test binary pattern validation"""
        # Valid patterns
        assert self.protocol.validate_binary_pattern("10101010") is True
        assert self.protocol.validate_binary_pattern("00000000") is True
        assert self.protocol.validate_binary_pattern("11111111") is True

        # Invalid patterns
        assert self.protocol.validate_binary_pattern("1010101") is False  # Too short
        assert self.protocol.validate_binary_pattern("101010101") is False  # Too long
        assert (
            self.protocol.validate_binary_pattern("1010101x") is False
        )  # Invalid character
        assert (
            self.protocol.validate_binary_pattern("12345678") is False
        )  # Invalid characters
        assert self.protocol.validate_binary_pattern(12345678) is False  # Not string

    def test_encode_ping_command(self):
        """Test PING command encoding"""
        result = self.protocol.encode_command("PING")
        assert result == "PING\n"

        # PING should not accept parameters
        with pytest.raises(
            RelayValidationError, match="PING command takes no parameters"
        ):
            self.protocol.encode_command("PING", 1)

    def test_encode_on_command(self):
        """Test ON command encoding"""
        # Valid ON commands
        assert self.protocol.encode_command("ON", 1) == "ON 1\n"
        assert self.protocol.encode_command("on", 8) == "ON 8\n"  # Case insensitive

        # Invalid ON commands
        with pytest.raises(
            RelayValidationError, match="ON command requires exactly one parameter"
        ):
            self.protocol.encode_command("ON")

        with pytest.raises(
            RelayValidationError, match="ON command requires exactly one parameter"
        ):
            self.protocol.encode_command("ON", 1, 2)

        with pytest.raises(RelayValidationError, match="Invalid relay number"):
            self.protocol.encode_command("ON", 9)

    def test_encode_off_command(self):
        """Test OFF command encoding"""
        # Valid OFF commands
        assert self.protocol.encode_command("OFF", 1) == "OFF 1\n"
        assert self.protocol.encode_command("off", 8) == "OFF 8\n"

        # Invalid OFF commands
        with pytest.raises(RelayValidationError, match="Invalid relay number"):
            self.protocol.encode_command("OFF", 0)

    def test_encode_status_command(self):
        """Test STATUS command encoding"""
        result = self.protocol.encode_command("STATUS")
        assert result == "STATUS\n"

        # STATUS should not accept parameters
        with pytest.raises(
            RelayValidationError, match="STATUS command takes no parameters"
        ):
            self.protocol.encode_command("STATUS", 1)

    def test_encode_all_command(self):
        """Test ALL command encoding"""
        # Valid ALL commands
        assert self.protocol.encode_command("ALL", "ON") == "ALL ON\n"
        assert self.protocol.encode_command("ALL", "OFF") == "ALL OFF\n"
        assert (
            self.protocol.encode_command("all", "on") == "ALL ON\n"
        )  # Case insensitive

        # Invalid ALL commands
        with pytest.raises(
            RelayValidationError, match="ALL command parameter must be ON or OFF"
        ):
            self.protocol.encode_command("ALL", "INVALID")

        with pytest.raises(
            RelayValidationError, match="ALL command requires exactly one parameter"
        ):
            self.protocol.encode_command("ALL")

    def test_encode_set_command(self):
        """Test SET command encoding"""
        # Valid SET commands
        assert self.protocol.encode_command("SET", "10101010") == "SET 10101010\n"
        assert self.protocol.encode_command("set", "00000000") == "SET 00000000\n"

        # Invalid SET commands
        with pytest.raises(RelayValidationError, match="Invalid binary pattern"):
            self.protocol.encode_command("SET", "1010101")  # Too short

        with pytest.raises(RelayValidationError, match="Invalid binary pattern"):
            self.protocol.encode_command("SET", "1010101x")  # Invalid character

    def test_encode_pulse_command(self):
        """Test PULSE command encoding"""
        # Valid PULSE commands
        assert self.protocol.encode_command("PULSE", 1, 500) == "PULSE 1 500\n"
        assert self.protocol.encode_command("pulse", 8, 1000) == "PULSE 8 1000\n"

        # Invalid PULSE commands
        with pytest.raises(RelayValidationError, match="Invalid relay number"):
            self.protocol.encode_command("PULSE", 9, 500)

        with pytest.raises(RelayValidationError, match="Invalid duration"):
            self.protocol.encode_command("PULSE", 1, 0)  # Too short

        with pytest.raises(RelayValidationError, match="Invalid duration"):
            self.protocol.encode_command("PULSE", 1, 15000)  # Too long

    def test_encode_info_command(self):
        """Test INFO command encoding"""
        result = self.protocol.encode_command("INFO")
        assert result == "INFO\n"

    def test_encode_uid_command(self):
        """Test UID command encoding"""
        result = self.protocol.encode_command("UID")
        assert result == "UID\n"

    def test_encode_name_command(self):
        """Test NAME command encoding"""
        # Valid NAME commands
        assert self.protocol.encode_command("NAME", 1, "TEST") == "NAME 1 TEST\n"
        assert self.protocol.encode_command("name", 8, "LIGHT") == "NAME 8 LIGHT\n"

        # Invalid NAME commands
        with pytest.raises(RelayValidationError, match="Invalid relay number"):
            self.protocol.encode_command("NAME", 9, "TEST")

        with pytest.raises(RelayValidationError, match="Invalid name"):
            self.protocol.encode_command("NAME", 1, "")  # Empty name

        with pytest.raises(RelayValidationError, match="Invalid name"):
            self.protocol.encode_command("NAME", 1, "A" * 33)  # Too long

    def test_encode_get_name_command(self):
        """Test GET NAME command encoding"""
        # Valid GET NAME commands
        assert self.protocol.encode_command("GET", "NAME", 1) == "GET NAME 1\n"
        assert self.protocol.encode_command("get", "name", 8) == "GET NAME 8\n"

        # Invalid GET commands
        with pytest.raises(RelayValidationError, match="GET subcommand must be NAME"):
            self.protocol.encode_command("GET", "STATUS", 1)

        with pytest.raises(RelayValidationError, match="Invalid relay number"):
            self.protocol.encode_command("GET", "NAME", 9)

    def test_encode_beep_command(self):
        """Test BEEP command encoding"""
        # Valid BEEP commands
        assert self.protocol.encode_command("BEEP") == "BEEP\n"
        assert self.protocol.encode_command("BEEP", 500) == "BEEP 500\n"

        # Invalid BEEP commands
        with pytest.raises(RelayValidationError, match="Invalid beep duration"):
            self.protocol.encode_command("BEEP", 0)  # Too short

        with pytest.raises(RelayValidationError, match="Invalid beep duration"):
            self.protocol.encode_command("BEEP", 6000)  # Too long

    def test_encode_buzz_command(self):
        """Test BUZZ command encoding"""
        # Valid BUZZ commands
        assert self.protocol.encode_command("BUZZ", "ON") == "BUZZ ON\n"
        assert self.protocol.encode_command("BUZZ", "OFF") == "BUZZ OFF\n"
        assert self.protocol.encode_command("buzz", "on") == "BUZZ ON\n"

        # Invalid BUZZ commands
        with pytest.raises(
            RelayValidationError, match="BUZZ command parameter must be ON or OFF"
        ):
            self.protocol.encode_command("BUZZ", "INVALID")

    def test_encode_tone_command(self):
        """Test TONE command encoding"""
        # Valid TONE commands
        assert self.protocol.encode_command("TONE", 1000, 500) == "TONE 1000 500\n"
        assert self.protocol.encode_command("tone", 440, 1000) == "TONE 440 1000\n"

        # Invalid TONE commands
        with pytest.raises(RelayValidationError, match="Invalid frequency"):
            self.protocol.encode_command("TONE", 30, 500)  # Too low

        with pytest.raises(RelayValidationError, match="Invalid frequency"):
            self.protocol.encode_command("TONE", 25000, 500)  # Too high

        with pytest.raises(RelayValidationError, match="Invalid duration"):
            self.protocol.encode_command("TONE", 1000, 0)  # Too short

        with pytest.raises(RelayValidationError, match="Invalid duration"):
            self.protocol.encode_command("TONE", 1000, 15000)  # Too long

    def test_encode_unknown_command(self):
        """Test unknown command encoding"""
        with pytest.raises(RelayValidationError, match="Unknown command"):
            self.protocol.encode_command("INVALID")

    def test_decode_response_success(self):
        """Test successful response decoding"""
        # Basic success responses
        success, data, error = self.protocol.decode_response("OK")
        assert success is True
        assert data is None
        assert error is None

        success, data, error = self.protocol.decode_response("PONG")
        assert success is True
        assert data == "PONG"
        assert error is None

        # Data responses
        success, data, error = self.protocol.decode_response("10101010")
        assert success is True
        assert data == "10101010"
        assert error is None

        success, data, error = self.protocol.decode_response(
            "WAVESHARE-PICO-RELAY-B,V1.0,8CH,UID:1234"
        )
        assert success is True
        assert data == "WAVESHARE-PICO-RELAY-B,V1.0,8CH,UID:1234"
        assert error is None

    def test_decode_response_error(self):
        """Test error response decoding"""
        success, data, error = self.protocol.decode_response("ERROR:INVALID_COMMAND")
        assert success is False
        assert data is None
        assert error == "INVALID_COMMAND"

        success, data, error = self.protocol.decode_response(
            "ERROR:INVALID_RELAY_NUMBER"
        )
        assert success is False
        assert data is None
        assert error == "INVALID_RELAY_NUMBER"

    def test_parse_status_response(self):
        """Test STATUS response parsing"""
        # Valid status responses
        states = self.protocol.parse_status_response("10101010")
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
        assert states == expected

        states = self.protocol.parse_status_response("00000000")
        expected = {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
        }
        assert states == expected

        states = self.protocol.parse_status_response("11111111")
        expected = {
            1: True,
            2: True,
            3: True,
            4: True,
            5: True,
            6: True,
            7: True,
            8: True,
        }
        assert states == expected

        # Invalid status responses
        with pytest.raises(RelayValidationError, match="Invalid status data"):
            self.protocol.parse_status_response("1010101")  # Too short

        with pytest.raises(RelayValidationError, match="Invalid status data"):
            self.protocol.parse_status_response("1010101x")  # Invalid character

    def test_parse_info_response(self):
        """Test INFO response parsing"""
        # Complete INFO response
        info = self.protocol.parse_info_response(
            "WAVESHARE-PICO-RELAY-B,V1.0,8CH,UID:ECD43B7502A23159"
        )
        expected = {
            "board_name": "WAVESHARE-PICO-RELAY-B",
            "version": "V1.0",
            "channels": "8CH",
            "uid": "ECD43B7502A23159",
        }
        assert info == expected

        # Partial INFO response
        info = self.protocol.parse_info_response("WAVESHARE-PICO-RELAY-B,V1.0")
        expected = {"board_name": "WAVESHARE-PICO-RELAY-B", "version": "V1.0"}
        assert info == expected

        # Minimal INFO response
        info = self.protocol.parse_info_response("BOARD")
        expected = {"board_name": "BOARD"}
        assert info == expected
