import datetime
import logging
import threading

import pytz

logger = logging.getLogger(__name__)

# Maximum time a sensor reading can be used for, in seconds
_FRESHNESS_THRESHOLD = 2
# Position of humidity value in the tuple returned from DHT22 read function.
_HUMIDITY_INDEX = 0
# Position of  temperature value in the tuple returned from DHT22 read function.
_TEMPERATURE_INDEX = 1

# Sensor calibration
TEMPERATURE_CORRECTION = -1.0
HUMIDITY_CORRECTION = 0.0


class CachingDHT22(object):
    """Wrapper around a DHT22 that caches sensor readings.

    Reads and returns temperature and humidity levels while also caching these
    values to ensure that the sensor is not polled at too high of a frequency.
    This class is thread-safe.
    """

    def __init__(self, dht22_read_func, clock):
        """Creates a new CachingDHT22 object.

        Args:
            dht22_read_func: A function that returns the temperature and
                humidity readings from a DHT22 sensor.
            clock: A clock interface
        """
        self._dht22_read_func = dht22_read_func
        self._clock = clock
        self._last_reading_time = datetime.datetime.min.replace(tzinfo=pytz.utc)
        self._last_reading = None
        self._lock = threading.Lock()

    def _read_dht22(self):
        """Returns current or recent temperature and humidity values.

        Returns cached values if the sensor has been polled recently enough,
        otherwise polls the sensor and returns current values.
        """
        with self._lock:
            now = self._clock.now()
            if (now - self._last_reading_time).total_seconds() >= (
                    _FRESHNESS_THRESHOLD):
                self._last_reading_time = now
                self._last_reading = self._dht22_read_func()
                logger.info('DHT22 raw reading = %s', self._last_reading)
            else:
                logger.info(
                    'read DHT22 too recently, returning cached reading = %s',
                    self._last_reading)

        return self._last_reading

    def humidity(self):
        """Returns a recent relative humidity reading."""
        humidity = self._read_dht22()[_HUMIDITY_INDEX]
        if (humidity):
            return humidity + HUMIDITY_CORRECTION
        else:
            return 0.0

    def temperature(self):
        """Returns a recent ambient temperature reading in Celsius."""
        temperature = self._read_dht22()[_TEMPERATURE_INDEX]
        if (temperature):
            return temperature + TEMPERATURE_CORRECTION
        else:
            return 0.0
