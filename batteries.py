import RPi.GPIO as GPIO
from time import sleep, time
from datetime import datetime as dt
from daqhats import mcc118, OptionFlags, HatIDs, HatError, hat_list
import subprocess
import os
import h5py
import logging


class Battery:
    battery_nr = None
    gpios = None
    gpios_available = {0: [19, 16],
                       1: [20, 21]}

    def __init__(self, battery_nr=0):
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

