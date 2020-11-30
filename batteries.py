try:
    import RPi.GPIO as GPIO
except ImportError:
    print('only DummyBatteries available')
    pass
import logging
log = logging.getLogger(__name__)

class DummyBatteries:
    def __init__(self):
        self.state = [True, True]  # default to measure mode (I'm assuming GPIO high is true

    def measure(self):
        log.debug('Batteries connected to amplifier')
        self.state = [True, True]

    def charge(self):
        log.debug('Batteries connected to charger')
        self.state = [False, False]

class Battery:
    gpios_available = {0: [19, 16],
                       1: [20, 21]}

    def __init__(self, battery_nr):
        if not (GPIO.getmode() == GPIO.BCM):
            GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.battery_nr = battery_nr
        self.gpios = self.gpios_available[self.battery_nr]

        for gpio in self.gpios:
            GPIO.setup(gpio, GPIO.OUT)

    def charge(self):
        for gpio in self.gpios:
            GPIO.output(gpio, GPIO.LOW)

    def measure(self):
        for gpio in self.gpios:
            GPIO.output(gpio, GPIO.HIGH)

    @property
    def state(self):
        gpio_state = []
        for gpio in self.gpios:
            gpio_state.append(GPIO.input(gpio))
        return gpio_state


class Batteries(Battery):
    battery_ids = [0, 1]
    batteries = {}

    def __init__(self):
        if not (GPIO.getmode() == GPIO.BCM):
            GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for b in self.battery_ids:
            self.batteries[b] = Battery(b)
        self.charge()
        logging.debug('Initialized batteries in charging state')

    def charge(self):
        for b in self.batteries:
            self.batteries[b].charge()

    def measure(self):
        for b in self.batteries:
            self.batteries[b].measure()

    @property
    def state(self):
        gpio_state = [self.batteries[b].state for b in self.batteries]
        return gpio_state

