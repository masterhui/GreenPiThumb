import logging
import yagmail

logger = logging.getLogger(__name__)

AUTH_PATH = "/root/auth.yagmail"


class EmailNotification(object):
    """Wrapper around yagmail

    Sends an email to the specified recipient.
    """

    def __init__(self, subject, body):
        """Creates a new EmailNotification object.

        Args:
            to: Email address of recipient
            subject: Email subject
            body: Body text of email
        """
        self._subject = subject
        self._body = body
        

    def send(self):
        """Sends an email via yagmail."""
        # Read credentials
        f = open(AUTH_PATH, 'r')
        user = f.readline().replace('\n', '')
        pw = f.readline().replace('\n', '')
        #print 'user=%s pw=%s' %(user, pw)

        # Register connection
        yag = yagmail.SMTP(user, pw)
        
        # Send the email
        yag.send(subject = self._subject, contents = self._body)
        logger.info('Notifcation email sent to %s' % user)
