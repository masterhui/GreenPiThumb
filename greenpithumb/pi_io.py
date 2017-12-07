import logging

logger = logging.getLogger(__name__)


class IO(object):
    """Wrapper for input and output on a Raspberry Pi board.

    This wraps the board and allows the caller to read or send signals to
    the Raspberry Pi's pins. No more than one instance of this class should
    exist at any given time.
    """

    def __init__(self, gpio):
        """Creates a new input/output wrapper.

        Args:
            gpio: Raspberry Pi GPIO module.
        """
        self._GPIO = gpio
        self._GPIO.setmode(self._GPIO.BCM)
        self._output_pins = set()
        self._input_pins = set()

    def turn_pin_on(self, pin):
        """Turns on a Raspberry Pi GPIO pin.

        Args:
            pin: Index of Raspberry Pi pin to turn on
        """
        #~ logger.info('turn_pin_on(%d)', pin)
        self._ensure_pin_is_output(pin)
        self._GPIO.output(pin, self._GPIO.HIGH)

    def turn_pin_off(self, pin):
        """Turns off a Raspberry Pi GPIO pin.

        Args:
            pin: Index of Raspberry Pi pin to turn off
        """
        #~ logger.info('turn_pin_off(%d)', pin)
        self._ensure_pin_is_output(pin)
        self._GPIO.output(pin, self._GPIO.LOW)
        
    def read_pin(self, pin):
        """Reads a Raspberry Pi GPIO pin.

        Args:
            pin: Index of Raspberry Pi pin to read
        """
        self._ensure_pin_is_input(pin)
        return self._GPIO.input(pin)        

    def _ensure_pin_is_output(self, pin):
        """Adds pin to output pin set if it is not already in it."""
        #~ logger.info('_ensure_pin_is_output(%d)', pin)
        #~ if pin in self._output_pins:
            #~ logger.info('******** EARLY EXIT ************')
            #~ return
        self._GPIO.setup(pin, self._GPIO.OUT)
        self._output_pins.add(pin)
        
    def _ensure_pin_is_input(self, pin):
        """Adds pin to input pin set if it is not already in it."""
        #~ if pin in self._input_pins:
            #~ return
        self._GPIO.setup(pin, self._GPIO.IN)
        self._input_pins.add(pin)        

    def close(self):
        """Cleans up the Raspberry Pi I/O interface.

        Should be called when use of the I/O interface is complete.
        """
        self._GPIO.cleanup()
