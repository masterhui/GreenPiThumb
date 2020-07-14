#!/usr/bin/env python

import yagmail
import argparse

AUTH_PATH = "/root/auth.yagmail"


def main(args):
    
    # Read credentials
    try:
        f = open(AUTH_PATH, 'r')
        user = f.readline().replace('\n', '')
        pw = f.readline().replace('\n', '')
        print 'user: %s\npw: %s' %(user, pw)
    except:
        print 'ERROR: Cannot open credentials file'
        return

    # Register connection
    try:
        yag = yagmail.SMTP(user, pw)
    except:
        print 'ERROR: Wrong username or password'
        return
    
    # Send the email
    try:
        yag.send(to = args.to, subject = args.subject, contents = args.body)
        print 'Notifcation email sent to: %s' % user
    except:
        print 'ERROR: Cannot send email using yagmail'
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPi Email Notification Diagnostic Test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-t',
        '--to',
        help='Email recipient')
    parser.add_argument(
        '-s',
        '--subject',
        help='Email subject', default="GreenPiThumb Email Notification Test")
    parser.add_argument(
        '-b',
        '--body',
        help='Email body')            
        
    main(parser.parse_args())
