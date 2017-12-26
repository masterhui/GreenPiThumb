import logging
import time

logger = logging.getLogger(__name__)


class SoilMoistureSensor(object):
    """Wrapper for a moisture sensor."""


    def __init__(self, adc, pi_io, channel, gpio_pin):
        """Creates a new SoilMoistureSensor instance.

        Args:
            adc: ADC(analog to digital) interface to receive analog signals from
                a Vegetronix VH400 soil moisture sensor.
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
        
        
    def calc_vwc(self, V):
        """Returns the Volumetric Water Content (VWC)
        Most curves can be approximated with linear segments of the form:

        y= m*x-b,

        where m is the slope of the line

        The VH400's Voltage to VWC curve can be approximated with 4 segents of the form:

        VWC= m*V-b

        where V is voltage.

        m= (VWC2 - VWC1)/(V2-V1)

        where V1 and V2 are voltages recorded at the respective VWC levels of VWC1 and VWC2. 
        After m is determined, the y-axis intercept coefficient b can be found by inserting one of the end points into the equation:

        b= m*v-VWC

        Voltage Range	Equation
        0 to 1.1V	VWC= 10*V-1
        1.1V to 1.3V	VWC= 25*V- 17.5
        1.3V to 1.82V	VWC= 48.08*V- 47.5
        1.82V to 2.2V	VWC= 26.32*V- 7.89

        Most soils have a holding capacity of less that 50%, so the curves stop at 2.2V which represents 50% VWC. Above 50% you can use an approximation as follows: 

        2.2V - 3.0V	VWC= 62.5*V - 87.5
        """
        VWC = 0.0
        
        if(V < 0.0):
            logger.warn('vh400 voltage below 0.0 volts: {0:0.2f} v'.format(V))
        elif(V >= 0.0 and V < 1.1):
            VWC = 10.0 * V - 1.0            
        elif(V >= 1.1 and V < 1.3):
            VWC = 25.0 * V - 17.5
        elif(V >= 1.3 and V < 1.82):
            VWC = 48.08 * V - 47.5
        elif(V >= 1.82 and V < 2.2):
            VWC = 26.32 * V - 7.89
        elif(V >= 2.2 and V < 3.0):
            VWC = 62.5 * V - 87.5
        elif(V >= 3.0):
            VWC = 62.5 * V - 87.5
            
        return VWC/2.0   # Divide by two based on measurement with dry and wet soil        
        

    def soil_moisture(self):
        """Returns the soil moisture level as volumetric water content (VWC).

        Takes a reading from the soil moisture sensor by powering the GPIO pin the
        sensor is connected to.
        """
        # Turn device power on
        self._pi_io.turn_pin_on(self._gpio_pin)
        
        # Sensor startup time
        time.sleep(2.0)   # Wait time in seconds

        # Take sensor reading
        raw_value = self._adc.read_adc(self._channel)
        logger.info('vh400 raw value = {}'.format(raw_value))
        
        # Convert to voltage
        voltage = raw_value / 100.0
        logger.info('vh400 voltage = {0:0.2f} v'.format(voltage))
            
        # Calculate volumetric water content from voltage        
        vwc = self.calc_vwc(voltage)
        logger.info('vh400 vwc reading = {0:0.1f} %'.format(vwc))
        
        # Sensor cooldown time
        #time.sleep(2.0)   # Wait time in seconds
        
        # Turn device power off
        self._pi_io.turn_pin_on(self._gpio_pin)
        
        return vwc
      
      
