try:
    import RPi.GPIO as GPIO
except ImportError:
    print('only DummyBatteries available')
    pass
import time

import logging
log = logging.getLogger(__name__)


class PushButton:
    '''
    Setup a PushButton and connect it to a GPIO as follows:
    pb = PushButton()
    GPIO.add_event_detect(26, GPIO.FALLING, callback=pb.button_readout, bouncetime=500)

    The latest event will be stored in button_pushed, and cleared once button_pushed is accessed.
    0 means no event, 1 means short press, 2 means long press.
    Any press shorter than long_threshold will be a short press
    Any press longer than long_threshold will be a long press
    '''
    def __init__(self, long_threshold=3.):
        self._button_pushed = 0  # 1 for short press, 2 for long press
        self.long_threshold = long_threshold

    @property
    def button_pushed(self):
        ret_val = self._button_pushed
        self._button_pushed = 0
        return ret_val

    def button_readout(self, channel):
        log.debug('Enter button readout')
        start_time = time.time()

        while GPIO.input(channel) == 0: # Wait for the button up
            pass
        log.debug('Button up')

        buttonTime = time.time() - start_time    # How long was the button down?

        if buttonTime < self.long_threshold:
            self.buttonStatus = 1  # 1 Short press
            log.debug('was short')
        else:
            self.buttonStatus = 2  # 2 Long press
            log.debug('was long')

        log.debug('Exit button push')
