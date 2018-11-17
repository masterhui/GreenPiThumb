#!/usr/bin/env python

import argparse
import time

import Adafruit_MCP3008
import RPi.GPIO as GPIO

CLK  = 18
MISO = 23
MOSI = 24
CS   = 25


def calc_vwc(V):
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
        print('[WARN] vh400 voltage below 0.0 volts: {0:0.1f}v'.format(V))
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
        

def main(args):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(args.gpio_pin, GPIO.OUT)

    mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
    
    # Turn device power on
    print('Turn device power on (pin={})'.format(args.gpio_pin))
    GPIO.output(args.gpio_pin, GPIO.HIGH)

    # Allow warm-up time
    time.sleep(1.0)
    try:
        while True:   
            # Take sensor reading
            raw_value = mcp.read_adc(args.channel)
            print('VH400 raw value = {}'.format(raw_value))
            
            # Convert to voltage
            voltage = raw_value / 100.0
            print('VH400 voltage = {0:0.2f} v'.format(voltage))
            
            # Calculate volumetric water content            
            vwc = calc_vwc(voltage)
            print('VH400 vwc = {0:0.1f} %\n'.format(vwc))
            
            time.sleep(1.0)   # Wait time in seconds            

    except KeyboardInterrupt:        
        # Turn device power off
        print('Turn device power off (pin={})'.format(args.gpio_pin))
        GPIO.output(args.gpio_pin, GPIO.LOW)           

    finally:
        print('GPIO cleanup')
        GPIO.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPiThumb Soil Moisture Diagnostic Test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--gpio_pin',
        type=int,
        help='Pin to power VH400 sensor',
        default=16)
    parser.add_argument(
        '-c',
        '--channel',
        type=int,
        help='ADC channel that the VH400 is plugged in to',
        default=7)
    main(parser.parse_args())
