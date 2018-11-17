#!/usr/bin/env python

import argparse
import time

import Adafruit_MCP3008
import RPi.GPIO as GPIO

CLK  = 18
MISO = 23
MOSI = 24
CS   = 25
WET_VALUE = 600
DRY_VALUE = 1000

def main(args):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(args.gpio_pin, GPIO.OUT)

    mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
    
    # Turn device power on
    print('Turn device power on (pin={})'.format(args.gpio_pin))
    GPIO.output(args.gpio_pin, GPIO.HIGH)
    
    # Sensor startup time
    print('Sensor startup')
    time.sleep(2.0)   # Wait time in seconds


    try:
        while True:   
            # Take sensor reading
            reading = mcp.read_adc(args.channel)
            print('Drain sensor reading = {}'.format(reading))
            
            # Decide if on or off            
            waterPresent = False
            mid_point = WET_VALUE + (DRY_VALUE - WET_VALUE) / 2
            if (reading > mid_point):
                waterPresent = False
            else:
                waterPresent = True
                
            print('Water present = {}\n'.format(waterPresent))
            
            time.sleep(1.0)  # Wait time in seconds            

    except KeyboardInterrupt:        
        # Turn device power off
        print('Turn device power off (pin={})'.format(args.gpio_pin))
        GPIO.output(args.gpio_pin, GPIO.LOW)           

    finally:
        print('GPIO cleanup')
        GPIO.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPiThumb Drain Sensor Diagnostic Test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--gpio_pin',
        type=int,
        help='Pin to power drain sensor',
        default=12)
    parser.add_argument(
        '-c',
        '--channel',
        type=int,
        help='ADC channel that the drain sensor is plugged in to',
        default=6)
    main(parser.parse_args())
