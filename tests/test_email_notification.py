#!/usr/bin/env python

import yagmail
import argparse

AUTH_PATH = "/root/auth.yagmail"


def main(args):
       
    # Read credentials
    f = open(AUTH_PATH, 'r')
    user = f.readline().replace('\n', '')
    pw = f.readline().replace('\n', '')
    #print 'user=%s pw=%s' %(user, pw)

    # Register connection
    yag = yagmail.SMTP(user, pw)    
    
    # Send the email
    yag.send(to = args.to, subject = args.subject, contents = args.body)     


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPiThumb Email Notification Diagnostic Test',
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
    parser.add_argument(
        '-u',
        '--username',
        help='The gmail user name for sending the email',
        required=True)                 
        
    main(parser.parse_args())
