"""
Hardware interface for teletype devices.

This module provides a platform-independent interface to physical teletype hardware.
It gracefully handles platforms where GPIO or serial hardware is not available.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import GPIO, but don't fail if not available
try:
    import RPi.GPIO as GPIO

    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    logger.debug("RPi.GPIO not available - GPIO features will be disabled")

# Serial should be available via pyserial
try:
    import serial

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logger.debug("pyserial not available - Serial features will be disabled")


class HardwareInterface:
    """
    Platform-independent hardware interface for teletype devices.

    This class provides methods to interact with physical teletype hardware
    via serial communication and GPIO control (when available).
    """

    def __init__(self, serial_port: Optional[str] = None, gpio_pin: Optional[int] = None):
        """
        Initialize the hardware interface.

        Args:
            serial_port: Serial port path (e.g., '/dev/ttyUSB0' or 'COM3')
            gpio_pin: GPIO pin number for control signals (BCM numbering)
        """
        self.serial_port = serial_port
        self.gpio_pin = gpio_pin
        self.serial_connection: Optional[serial.Serial] = None
        self._gpio_initialized = False

        self._check_capabilities()

    def _check_capabilities(self):
        """Check what hardware capabilities are available on this platform."""
        capabilities = []

        if SERIAL_AVAILABLE and self.serial_port:
            capabilities.append("serial")

        if GPIO_AVAILABLE and self.gpio_pin:
            capabilities.append("gpio")

        if not capabilities:
            logger.warning(
                "No hardware capabilities available - running in software-only mode"
            )
        else:
            logger.info(f"Hardware capabilities available: {', '.join(capabilities)}")

    def initialize(self) -> bool:
        """
        Initialize hardware connections.

        Returns:
            True if initialization successful, False otherwise
        """
        success = True

        # Initialize serial connection
        if SERIAL_AVAILABLE and self.serial_port:
            try:
                self.serial_connection = serial.Serial(
                    port=self.serial_port,
                    baudrate=110,  # Standard teletype baudrate
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1,
                )
                logger.info(f"Serial connection established on {self.serial_port}")
            except Exception as e:
                logger.error(f"Failed to initialize serial connection: {e}")
                success = False

        # Initialize GPIO
        if GPIO_AVAILABLE and self.gpio_pin:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.gpio_pin, GPIO.OUT)
                self._gpio_initialized = True
                logger.info(f"GPIO initialized on pin {self.gpio_pin}")
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {e}")
                success = False

        return success

    def send_data(self, data: bytes) -> bool:
        """
        Send data to the teletype device.

        Args:
            data: Bytes to send to the device

        Returns:
            True if send successful, False otherwise
        """
        if not SERIAL_AVAILABLE or not self.serial_connection:
            logger.debug("Serial not available - data not sent")
            return False

        try:
            self.serial_connection.write(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            return False

    def receive_data(self, size: int = 1) -> Optional[bytes]:
        """
        Receive data from the teletype device.

        Args:
            size: Number of bytes to read

        Returns:
            Received bytes or None if error/unavailable
        """
        if not SERIAL_AVAILABLE or not self.serial_connection:
            logger.debug("Serial not available - cannot receive data")
            return None

        try:
            return self.serial_connection.read(size)
        except Exception as e:
            logger.error(f"Failed to receive data: {e}")
            return None

    def set_gpio_state(self, state: bool) -> bool:
        """
        Set GPIO pin state.

        Args:
            state: True for HIGH, False for LOW

        Returns:
            True if successful, False otherwise
        """
        if not GPIO_AVAILABLE or not self._gpio_initialized:
            logger.debug("GPIO not available")
            return False

        try:
            GPIO.output(self.gpio_pin, GPIO.HIGH if state else GPIO.LOW)
            return True
        except Exception as e:
            logger.error(f"Failed to set GPIO state: {e}")
            return False

    def cleanup(self):
        """Cleanup hardware resources."""
        if self.serial_connection:
            try:
                self.serial_connection.close()
                logger.info("Serial connection closed")
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")

        if GPIO_AVAILABLE and self._gpio_initialized:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
