try:
    import RPi.GPIO as GPIO
except ImportError:
    print('only DummyBatteries available')
    pass

class IndicatorLights:
    def __init__(self, red, green):
        self.RED = red
        self.GREEN = green

        if not (GPIO.getmode() == GPIO.BCM):  # Use BCM numbering
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RED, GPIO.OUT)
        GPIO.setup(self.GREEN, GPIO.OUT)

    def _set_leds(self, red_val, green_val):
        GPIO.output(self.RED, red_val)
        GPIO.output(self.GREEN, green_val)

    def off(self):
        self._set_leds(0, 0)

    def ready(self):
        self._set_leds(0, 1)

    def busy(self):
        self._set_leds(1, 0)

    def both(self):
        self._set_leds(0, 0)