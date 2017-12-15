# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class TemperatureSensor(object):
    """Wrapper for a temperature sensor."""

    def __init__(self, dht22):
        """Creates a new TemperatureSensor wrapper.

        Args:
            dht22: DHT22 sensor instance that returns temperature readings.
        """
        self._dht22 = dht22

    def temperature(self):
        """Returns ambient temperature in Celcius."""
        temperature = self._dht22.temperature()
        logging.info('temperature reading = {0:0.1f} °C'.format(temperature))
        return temperature
