import logging
import time

logger = logging.getLogger(__name__)

WET_VALUE = 600
DRY_VALUE = 1000


class DrainSensor(object):
    """Wrapper for a moisture sensor."""


    def __init__(self, adc, pi_io, channel, gpio_pin):
        """Creates a new DrainSensor instance.

        Args:
            adc: ADC(analog to digital) interface to receive analog signals from
                a drain sensor.
            pi_io: Raspberry Pi I/O interface.
            channel: ADC channel to which the moisture sensor is connected. Must
                be an int between 0 and 7.
            gpio_pin: The Raspberry Pi GPIO pin that the moisture sensor is
                connected to. Must be an int between 2 and 27.
        """
        self._adc = adc
        self._pi_io = pi_io
        self._channel = channel
        self._gpio_pin = gpio_pin


    def water_present(self):
        """Returns whether there is water present at the sensor.

        Takes a reading from the drain sensor by powering the GPIO pin the
        sensor is connected to.
        """
        # Turn device power on
        self._pi_io.turn_pin_on(self._gpio_pin)
        
        # Sensor startup time
        time.sleep(2.0)   # Wait time in seconds

        # Take sensor reading
        reading = self._adc.read_adc(self._channel)
        logger.info('drain sensor reading = {}'.format(reading))
        
        # Decide if on or off            
        water_present = False
        mid_point = WET_VALUE + (DRY_VALUE - WET_VALUE) / 2
        if (reading > mid_point):
            water_present = False
        else:
            water_present = True
            
        logger.info('waterPresent = {}\n'.format(water_present))
               
        # Turn device power off
        self._pi_io.turn_pin_on(self._gpio_pin)
        
        return water_present
      
      
