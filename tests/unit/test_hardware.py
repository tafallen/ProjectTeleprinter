"""
Unit tests for hardware interface module.
"""
import pytest

from telex.hardware.interface import HardwareInterface, GPIO_AVAILABLE, SERIAL_AVAILABLE


def test_hardware_interface_initialization():
    """Test hardware interface can be initialized without hardware."""
    # Should not raise an error even if hardware is not available
    interface = HardwareInterface()
    assert interface is not None


def test_hardware_interface_with_serial_port():
    """Test hardware interface with serial port configuration."""
    interface = HardwareInterface(serial_port="/dev/ttyUSB0")

    assert interface.serial_port == "/dev/ttyUSB0"
    assert interface.serial_connection is None  # Not initialized yet


def test_hardware_interface_with_gpio():
    """Test hardware interface with GPIO configuration."""
    interface = HardwareInterface(gpio_pin=17)

    assert interface.gpio_pin == 17
    assert not interface._gpio_initialized  # Not initialized yet


def test_hardware_interface_context_manager():
    """Test hardware interface can be used as context manager."""
    with HardwareInterface() as interface:
        assert interface is not None


def test_send_data_without_hardware():
    """Test sending data fails gracefully without hardware."""
    interface = HardwareInterface()
    result = interface.send_data(b"test")

    # Should return False but not raise an exception
    assert result is False


def test_receive_data_without_hardware():
    """Test receiving data fails gracefully without hardware."""
    interface = HardwareInterface()
    result = interface.receive_data()

    # Should return None but not raise an exception
    assert result is None


def test_set_gpio_state_without_hardware():
    """Test GPIO control fails gracefully without hardware."""
    interface = HardwareInterface()
    result = interface.set_gpio_state(True)

    # Should return False but not raise an exception
    assert result is False


def test_cleanup_without_hardware():
    """Test cleanup works without hardware."""
    interface = HardwareInterface()
    # Should not raise an exception
    interface.cleanup()


@pytest.mark.skipif(not SERIAL_AVAILABLE, reason="pyserial not available")
def test_serial_available():
    """Test that serial module is detected when available."""
    assert SERIAL_AVAILABLE is True
