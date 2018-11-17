#!/usr/bin/env python

import argparse
import time
import RPi.GPIO as GPIO

DISTANCE_CORRECTION_FACTOR =  3.0  # [cm]


def main(args):
      
    try:
        # Setup
        GPIO.setmode(GPIO.BCM)

        while True:
            timeout_occurred = False
            
            GPIO.setup(args.pin, GPIO.OUT)
            # Set to low
            GPIO.output(args.pin, False)

            # Sleep 2 micro-seconds
            time.sleep(0.000002)

            # Set high
            GPIO.output(args.pin, True)

            # Sleep 5 micro-seconds
            time.sleep(0.000005)

            # Set low
            GPIO.output(args.pin, False)

            # Set to input
            GPIO.setup(args.pin, GPIO.IN)

            # Count microseconds that SIG was high
            timeout = time.time() + 1.0   # 1 second from now
            while GPIO.input(args.pin) == 0:
                starttime = time.time()
                if (time.time() > timeout):
                    timeout_occurred = True
                    break

            timeout = time.time() + 1.0   # 1 second from now
            while GPIO.input(args.pin) == 1:
                endtime = time.time()
                if (time.time() > timeout):
                    timeout_occurred = True
                    break            

            if timeout_occurred:
                print 'Timeout while sonar sensor'         
            else:
                duration = endtime - starttime            
                # The speed of sound is 340 m/s or 29 microseconds per centimeter.
                # The ping travels out and back, so to find the distance of the
                # object we take half of the distance travelled.
                # distance = duration / 29 / 2
                distance = (duration * 34000 / 2.0) - DISTANCE_CORRECTION_FACTOR
                print 'distance: {0:0.2f} cm'.format(distance)
                time.sleep(0.5)
    finally:
      GPIO.cleanup()      


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPiThumb Sonar Sensor Diagnostic Test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-p',
        '--pin',
        type=int,
        help='GPIO pin that is connected to the sonar sensor', default=20)
    main(parser.parse_args())
