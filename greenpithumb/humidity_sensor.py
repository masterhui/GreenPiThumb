import logging

logger = logging.getLogger(__name__)


class HumiditySensor(object):
    """Wrapper for a humidity sensor."""

    def __init__(self, dht22):
        """Creates a new HumiditySensor wrapper.

        Args:
            dht22: DHT22 sensor instance that returns relative humidity
                readings.
        """
        self._dht22 = dht22

    def humidity(self):
        """Returns relative humidity level."""
        humidity = self._dht22.humidity()
        logger.info('humidity reading = {0:0.1f} %'.format(humidity))
        return humidity
