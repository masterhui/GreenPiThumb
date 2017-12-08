import logging

logger = logging.getLogger(__name__)


class SoilMoistureSensor(object):
    """Wrapper for a moisture sensor."""

    def __init__(self, adc, pi_io, channel, gpio_pin):
        """Creates a new SoilMoistureSensor instance.

        Args:
            adc: ADC(analog to digital) interface to receive analog signals from
                moisture sensor.
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

    def soil_moisture(self):
        """Returns the soil moisture level.

        Takes a reading from the moisture sensor by powering the GPIO pin the
        sensor is connected to.
        """
        
        # Measured sensor max and min value constants
        Vair = 802.0
        Vwet = 393.0

        # Read raw value        
        moisture_raw = self._adc.read_adc(self._channel)
        #logger.info('soil moisture reading raw= %d', moisture_raw)
            
        # Invert, calibrate sensor range and make the value a percentage
        moisture_corrected = ((Vair - moisture_raw) / (Vair - Vwet)) * 100
        logger.info('soil moisture reading = %d', moisture_corrected)
        
        return moisture_corrected
