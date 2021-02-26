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
    def __init__(self, long_threshold=2.):
        self._button_pushed = 0  # 1 for short press, 2 for long press
        self._last_value_time = 0
        self.memory = 5.
        self.long_threshold = long_threshold
        self._debounce = 0.5  # button_up debounce

    @property
    def button_pushed(self):
        # if the last event is too old, reset output to 0
        if self._last_value_time < time.time() - self.memory:
            self._button_pushed = 0
        # log.debug('button value is {}'.format(self._button_pushed))
        return self._button_pushed

    def button_readout(self, channel):
        log.debug('Enter button readout')
        if time.time() - self._last_value_time > self._debounce:
            log.debug('Debouncing on button up')
            return

        start_time = time.time()

        while GPIO.input(channel) == 0: # Wait for the button up
            pass

        buttonTime = time.time() - start_time    # How long was the button down?
        log.debug('Button up. press length: {:.1f}'.format(buttonTime))

        if buttonTime < self.long_threshold:
            self._button_pushed = 1  # 1 Short press
            log.debug('was short')
        else:
            self._button_pushed = 2  # 2 Long press
            log.debug('was long')

        self._last_value_time = time.time()  # remember when the last event happened
        log.debug('Exit button push')
