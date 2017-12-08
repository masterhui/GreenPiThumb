import RPi.GPIO as GPIO
import time
import logging

logger = logging.getLogger(__name__)

RESERVOIR_FULL = 3.0     # [cm]
RESERVOIR_EMPTY = 40.0   # [cm]


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
        self._last_reading = None

    def water_level(self):
        """Returns the water level.

        Takes a reading from the water level sensor
        """
        timeout_occurred = False
        distance = 0
        starttime = 0
        endtime = 0
        
        # Set to low
        self._pi_io.turn_pin_off(self._gpio_pin)

        # Sleep 2 micro-seconds
        time.sleep(0.000002)

        # Set high
        self._pi_io.turn_pin_on(self._gpio_pin)

        # Sleep 5 micro-seconds
        time.sleep(0.000005)

        # Set low
        self._pi_io.turn_pin_off(self._gpio_pin)

        # Count microseconds that SIG was high
        timeout = time.time() + 1   # 1 second from now        
        while self._pi_io.read_pin(self._gpio_pin) == 0:
            starttime = time.time()
            if (time.time() > timeout):
                timeout_occurred = True
                break

        timeout = time.time() + 1   # 1 second from now
        while self._pi_io.read_pin(self._gpio_pin) == 1:
            endtime = time.time()
            if (time.time() > timeout):
                timeout_occurred = True
                break            

        if timeout_occurred:
            logger.error('Timeout while reading water level')
            return 0
        else:
            duration = endtime - starttime
            # The speed of sound is 340 m/s or 29 microseconds per centimeter.
            # The ping travels out and back, so to find the distance of the
            # object we take half of the distance travelled.
            # distance = duration / 29 / 2
            distance = duration * 34000.0 / 2.0
            
            if ( (distance > RESERVOIR_EMPTY*1.1) or (distance < RESERVOIR_FULL*0.9) ):
                logger.error('invalid water level reading (%d), discarding measurement', distance)
                return 0
            else:
                # Invert, calibrate sensor range and make the value a percentage
                fill_percentage = ((RESERVOIR_EMPTY - distance) / (RESERVOIR_EMPTY - RESERVOIR_FULL)) * 100.0
                logger.info('water level reading = %d', fill_percentage)
                self._last_reading = fill_percentage
                return fill_percentage
