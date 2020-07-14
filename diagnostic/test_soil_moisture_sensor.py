#!/usr/bin/env python

import argparse
import time

import Adafruit_MCP3008
import RPi.GPIO as GPIO

CLK  = 18
MISO = 23
MOSI = 24
CS   = 25


def main(args):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(args.gpio_pin, GPIO.OUT)

    mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

    try:
        while True:
            GPIO.output(args.gpio_pin, GPIO.HIGH)
            moisture_raw = mcp.read_adc(args.channel)
            #~ print 'Soil mositure level: %d' % reading
            
            # Measured sensor max and min value constants
            Vair = 802.0
            Vwet = 393.0            
            
            # Invert, calibrate sensor range and make the value a percentage
            moisture_corrected = ((Vair - moisture_raw) / (Vair - Vwet)) * 100.0
            print('soil moisture raw = {}'.format(moisture_raw))            
            print('soil moisture corrected = {0:0.1f} %'.format(moisture_corrected))            
            
            GPIO.output(args.gpio_pin, GPIO.LOW)
            time.sleep(0.5)
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPiThumb Soil Moisture Diagnostic Test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--gpio_pin',
        type=int,
        help='Pin to power moisture sensor',
        default=16)
    parser.add_argument(
        '-c',
        '--channel',
        type=int,
        help='ADC channel that moisture sensor is plugged in to',
        default=7)
    main(parser.parse_args())
