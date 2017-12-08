import logging
import email_notification

logger = logging.getLogger(__name__)

# Pump rate in mL/s (4.3 L/min)
_PUMP_RATE_ML_PER_SEC = 1433.0 / 60.0

# Default amount of water to add to the plant (in mL) when pump manager detects
# low soil moisture.
DEFAULT_PUMP_AMOUNT = 200

# Send email notification if water level drops below this value (in cm)
WATER_LEVEL_THRESHOLD = 20


class Pump(object):
    """Wrapper for a Seaflo 12V water pump."""

    def __init__(self, pi_io, clock, pump_pin, water_level_sensor):
        """Creates a new Pump wrapper.

        Args:
            pi_io: Raspberry Pi I/O interface.
            clock: A clock interface.
            pump_pin: Raspberry Pi pin to which the pump is connected.
        """
        self._pi_io = pi_io
        self._clock = clock
        self._pump_pin = pump_pin
        self._water_level_sensor = water_level_sensor

    def pump_water(self, amount_ml):
        """Pumps the specified amount of water.

        Args:
            amount_ml: Amount of water to pump (in mL).

        Raises:
            ValueError: The amount of water to be pumped is invalid.
        """
        if amount_ml == 0.0:
            return
        elif amount_ml < 0.0:
            raise ValueError('Cannot pump a negative amount of water')
        else:
            logger.info('turning pump on (with GPIO pin %d)', self._pump_pin)
            self._pi_io.turn_pin_on(self._pump_pin)

            wait_time_seconds = amount_ml / _PUMP_RATE_ML_PER_SEC
            self._clock.wait(wait_time_seconds)

            logger.info('turning pump off (with GPIO pin %d)', self._pump_pin)
            self._pi_io.turn_pin_off(self._pump_pin)
            logger.info('pumped %.f mL of water', amount_ml)
            
            #~ if self._water_level_sensor._last_reading < WATER_LEVEL_THRESHOLD:
                #~ logger.info("True")
            
            # Read water level and check if a notification email should be sent
            if self._water_level_sensor._last_reading < WATER_LEVEL_THRESHOLD:
                subject = "GreenPiThumb low water level"
                body = "The water reservoir fill level has dropped below the set alert threshold of " + str(WATER_LEVEL_THRESHOLD) + " cm.\n\n" + \
                       "The current fill level is " + str(int(self._water_level_sensor._last_reading)) + " cm."
                logger.info("Low water level detected: %d cm (threshold=%d cm), sending notification email" % (self._water_level_sensor._last_reading, WATER_LEVEL_THRESHOLD))
                notifier = email_notification.EmailNotification(subject, body)
                notifier.send()
        return


class PumpManager(object):
    """Pump Manager manages the water pump."""

    def __init__(self, pump, pump_scheduler, moisture_threshold, pump_amount,
                 timer):
        """Creates a PumpManager object, which manages a water pump.

        Args:
            pump: A pump instance, which supports water pumping.
            pump_scheduler: A pump scheduler instance that controls the time
                periods in which the pump can be run.
            moisture_threshold: Soil moisture threshold. If soil moisture is
                below this value, manager pumps water on pump_if_needed calls.
            pump_amount: Amount (in mL) to pump every time the water pump runs.
            timer: A timer that counts down until the next forced pump. When
                this timer expires, the pump manager runs the pump once,
                regardless of the moisture level.
        """
        self._pump = pump
        self._pump_scheduler = pump_scheduler
        self._moisture_threshold = moisture_threshold
        self._pump_amount = pump_amount
        self._timer = timer

    def pump_if_needed(self, moisture):
        """Run the water pump if there is a need to run it.

        Args:
            moisture: Soil moisture level

        Returns:
            The amount of water pumped, in mL.
        """
        if self._should_pump(moisture):
            self._pump.pump_water(self._pump_amount)
            self._timer.reset()
            return self._pump_amount

        return 0

    def _should_pump(self, moisture):
        """Returns True if the pump should be run."""
        if not self._pump_scheduler.is_running_pump_allowed():
            return False
        return (moisture < self._moisture_threshold) or self._timer.expired()


class PumpScheduler(object):
    """Controls when the pump is allowed to run."""

    def __init__(self, local_clock, sleep_windows):
        """Creates new PumpScheduler instance.

        Args:
            local_clock: A local clock interface
            sleep_windows: A list of 2-tuples, each representing a sleep window.
                Tuple items are datetime.time objects.
        """
        self._local_clock = local_clock
        self._sleep_windows = sleep_windows

    def is_running_pump_allowed(self):
        """Returns True if OK to run pump, otherwise False.

        Pump is not allowed to run from the start of a sleep window (inclusive)
        to the end of a sleep window (exclusive).
        """
        current_time = self._local_clock.now().time()

        for sleep_time, wake_time in self._sleep_windows:
            # Check if sleep window wraps midnight.
            if wake_time < sleep_time:
                if current_time >= sleep_time or current_time < wake_time:
                    return False
            else:
                if sleep_time <= current_time < wake_time:
                    return False

        return True
