import logging
import email_notification
import time

logger = logging.getLogger(__name__)

# Pump rate in ml/s
_PUMP_RATE_ML_PER_SEC = 1433.0 / 60.0   # Calibration measurement at 1.43 L/min

# Amount of water to be continuously pumped before stopping to allow water to drain and soak
INTERVAL_PUMP_AMOUNT = 500   # In [ml]

# Interval duration to wait between consecutive pump runs
INTERVAL_DURATION = 60   # In [s]

# Send email notification if water level drops below this value [l]
WATER_LEVEL_THRESHOLD = 7.5


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
            amount_ml: Amount of water to pump (in ml).

        Raises:
            ValueError: The amount of water to be pumped is invalid.
        """
        if amount_ml == 0.0:
            return
        elif amount_ml < 0.0:
            raise ValueError('Cannot pump a negative amount of water')
        else:
            logger.info('Turning pump on (with GPIO pin %d)', self._pump_pin)
            self._pi_io.turn_pin_on(self._pump_pin)

            wait_time_seconds = amount_ml / _PUMP_RATE_ML_PER_SEC
            self._clock.wait(wait_time_seconds)

            logger.info('Turning pump off (with GPIO pin %d)', self._pump_pin)
            self._pi_io.turn_pin_off(self._pump_pin)
            logger.info('Pumped %.f ml of water', amount_ml)

        return


class PumpManager(object):
    """Pump Manager manages the water pump."""

    def __init__(self, pump, pump_scheduler, moisture_threshold, total_pump_amount,
                 timer):
        """Creates a PumpManager object, which manages a water pump.

        Args:
            pump: A pump instance, which supports water pumping.
            pump_scheduler: A pump scheduler instance that controls the time
                periods in which the pump can be run.
            moisture_threshold: Soil moisture threshold. If soil moisture is
                below this value, manager pumps water on pump_if_needed calls.
            total_pump_amount: Total amount (in ml) to pump every time the water pump runs.
            timer: A timer that counts down until the next forced pump. When
                this timer expires, the pump manager runs the pump once,
                regardless of the moisture level.
        """
        self._pump = pump
        self._pump_scheduler = pump_scheduler
        self._moisture_threshold = moisture_threshold
        self._total_pump_amount = total_pump_amount
        self._timer = timer
        self._pump_event_in_progress = False
        
    def pump_event_in_progress():
        return self._pump_event_in_progress

    def pump_if_needed(self, moisture, drain_sensor):
        """Run the water pump if required.

        Args:
            moisture: Soil moisture level.
            drain_sensor: Interface to the drain sensor.

        Returns:
            The amount of water pumped, in ml.
        """
        accumulated_pump_amount = 0
        i = 0
        if self.should_pump(moisture):
            # Loop until total water amount to be pumped is reached
            self._pump_event_in_progress = True
            
            while(True):
                accumulated_pump_amount += INTERVAL_PUMP_AMOUNT
                i += 1                 
                logger.info("({}.) Pumping {} ml of water ({} ml of {} ml done)".format(i, INTERVAL_PUMP_AMOUNT, accumulated_pump_amount, self._total_pump_amount))
                self._pump.pump_water(INTERVAL_PUMP_AMOUNT)
                
                # Check fail conditions
                if(accumulated_pump_amount >= self._total_pump_amount):
                    logger.info("Total pump amount reached, end pump task")
                    break
                if(drain_sensor.water_present()):
                    logger.info("___Water detected by drain sensor, end pump task___")
                    break                    
                
                logger.info("Sleep for {} s to allow water to drain and soak".format(INTERVAL_DURATION))
                time.sleep(INTERVAL_DURATION)
                logger.info("Continue water pump event...")             
            
            self._pump_event_in_progress = False
            logger.info("==> Pump event complete, total amount pumped {} ml".format(accumulated_pump_amount))
            self.low_water_notification() 
            
        return accumulated_pump_amount

    
    def low_water_notification(self):    
        """
        Read water level and check if a notification email should be sent
        """
        if (self._water_level_sensor.water_level() < WATER_LEVEL_THRESHOLD):
            subject = "GreenPiThumb low water tank level"
            body = "The water tank fill level has dropped below the set alert threshold of {0:0.1f} liters.\n\n".format(WATER_LEVEL_THRESHOLD) + \
                   "The current fill level is {0:0.1f} liters.".format(self._water_level_sensor._last_reading)
            logger.info("Low water tank level detected: {0:0.1f} liters (threshold={0:0.1f} liters), sending notification email".format(self._water_level_sensor._last_reading, WATER_LEVEL_THRESHOLD))
            notifier = email_notification.EmailNotification(subject, body)
            notifier.send()      


    def should_pump(self, moisture):
        """Returns True if the pump should be run."""
        retVal = False

        # Collect pumping criteria        
        is_sleep_window = self._pump_scheduler.is_sleep_window()
        timer_expired = self._timer.expired()
        moisture_below_threshold = (moisture < self._moisture_threshold)
        pump_event_in_progress = self._pump_event_in_progress
        
        # Debug output
        logger.info("[should_pump] is_sleep_window = " + str(is_sleep_window))
        logger.info("[should_pump] timer_expired = " + str(timer_expired))
        logger.info("[should_pump] moisture_below_threshold = " + str(moisture_below_threshold))
        logger.info("[should_pump] pump_event_in_progress = " + str(pump_event_in_progress))
        
        # Determine whether we need to pump
        if( (timer_expired or moisture_below_threshold) and not (pump_event_in_progress or is_sleep_window) ):
            retVal = True
        else:
            retVal = False
            
        logger.info("[should_pump] retVal = " + str(retVal))
        return retVal      


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

    def is_sleep_window(self):
        """Returns True if we're currently within the sleep time window
          and the pump must not run, otherwise False.

        Pump is not allowed to run from the start of a sleep window (inclusive)
        to the end of a sleep window (exclusive).
        """
        current_time = self._local_clock.now().time()

        for sleep_time, wake_time in self._sleep_windows:
            # Check if sleep window wraps midnight.
            if wake_time < sleep_time:
                if current_time >= sleep_time or current_time < wake_time:
                    return True
            else:
                if sleep_time <= current_time < wake_time:
                    return True

        return False
