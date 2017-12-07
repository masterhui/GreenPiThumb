import RPi.GPIO as GPIO
import time
import logging

logger = logging.getLogger(__name__)


class WaterLevelSensor(object):
    """Wrapper for a sonar sensor."""

    def __init__(self, pi_io, gpio_pin):
        """Creates a new WaterLevelSensor instance.

        Args:
            pi_io: Raspberry Pi I/O interface.
            gpio_pin: The Raspberry Pi GPIO pin that the ultra sonic water 
                level sensor isconnected to. Must be an int between 2 and 27.
        """
        self._pi_io = pi_io
        self._gpio_pin = gpio_pin

    def water_level(self):
        """Returns the water level.

        Takes a reading from the water level sensor
        """
        
        # Set to low
        #GPIO.setup(11, GPIO.OUT)
        #GPIO.output(11, False)
        self._pi_io.turn_pin_off(self._gpio_pin)

        # Sleep 2 micro-seconds
        time.sleep(0.000002)

        # Set high
        #GPIO.output(11, True)
        self._pi_io.turn_pin_on(self._gpio_pin)

        # Sleep 5 micro-seconds
        time.sleep(0.000005)

        # Set low
        #GPIO.output(11, False)
        self._pi_io.turn_pin_off(self._gpio_pin)

        # Set to input
        #GPIO.setup(11, GPIO.IN)

        # Count microseconds that SIG was high
        while self._pi_io.read_pin(self._gpio_pin) == 0:
          starttime = time.time()

        while self._pi_io.read_pin(self._gpio_pin) == 1:
          endtime = time.time()

        duration = endtime - starttime
        # The speed of sound is 340 m/s or 29 microseconds per centimeter.
        # The ping travels out and back, so to find the distance of the
        # object we take half of the distance travelled.
        # distance = duration / 29 / 2
        distance = duration * 34000 / 2
        #print distance, "cm"
        logger.info('water level reading corrected = %d', distance)

        return distance
