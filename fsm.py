# A finite state machine for controlling the raspberry pi vibration control
import RPi.GPIO as GPIO
from push_button import PushButton
from indicator_lights import IndicatorLights
from vibration_station import VibrationPi
import time
import os

import logging
log = logging.getLogger(__name__)

# TODO: Add filename option to config. If omitted, use date as name
# TODO: Clean up main. Make the FSM its own class
# TODO: make sure shutdown actually shuts down


class VibrationFSM:
    AUTO_MODE_INITIALIZE = 0
    AUTO_MODE_WAIT = 1
    AUTO_MODE_MEASURE = 2

    MANUAL_MODE_INITIALIZE = 3
    MANUAL_MODE_WAIT = 4
    MANUAL_MODE_MEASURE = 5

    CHARGE_INITIALIZE = 7
    CHARGE = 8
    SHUTDOWN = 9
    state_names = {0: 'AUTO_MODE_INITIALIZE',
               1: 'AUTO_MODE_WAIT',
               2: 'AUTO_MODE_MEASURE',
               3: 'MANUAL_MODE_INITIALIZE',
               4: 'MANUAL_MODE_WAIT',
               5: 'MANUAL_MODE_MEASURE',
               7: 'CHARGE_INITIALIZE',
               8: 'CHARGE',
               9: 'SHUTDOWN',
               }
    
    def __init__(self, config_file_auto, config_file_manual):
        # config files
        self.config_file_auto = config_file_auto
        self.config_file_manual = config_file_manual

        print('Using config files: {} and {}'.format(config_file_auto.split('/')[-1],
                                                     config_file_manual.split('/')[-1]))
        log.info('Using config files: {} and {}'.format(config_file_auto.split('/')[-1],
                                                     config_file_manual.split('/')[-1]))

        # Setup connection to hardware
        if not (GPIO.getmode() == GPIO.BCM):  # Use BCM numbering
            GPIO.setmode(GPIO.BCM)
        
        self.indicator_lights = IndicatorLights(red=5, green=6)
        
        self.push_button = PushButton()
        self.push_button_pin = 2
        GPIO.setup(self.push_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.push_button_pin, GPIO.FALLING,
                              callback=self.push_button.button_readout, bouncetime=500)
        
        self.manual_switch_pin = 3
        GPIO.setup(self.manual_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # FSM initialization and running
        self.current_state = None
        self.next_state = self.AUTO_MODE_INITIALIZE

        self.vibration_pi = None

        # Store the position of the auto/man switch when charging.
        # This is required to know when we're switching away from it
        self.switch_state_on_charge_init = None

    def run(self):
        
        while True:
            time.sleep(0.05)
            # What state did we just transition to?
            if self.next_state is not None:
                self.current_state = self.next_state
                log.info('Entering state {}'.format(self.state_names[self.next_state]))
        
            self.next_state = None
        
            # What needs to be done in current state
            if self.current_state == self.AUTO_MODE_INITIALIZE:
                self.indicator_lights.off()
                self.vibration_pi = VibrationPi(self.config_file_auto)
        
                self.next_state = self.AUTO_MODE_WAIT
                continue
        
            elif self.current_state == self.AUTO_MODE_WAIT:
                self.indicator_lights.ready()
        
                if self.push_button.button_pushed == 2:
                    self.next_state = self.CHARGE_INITIALIZE
                    continue
        
                if GPIO.input(self.manual_switch_pin) == GPIO.HIGH:
                    self.next_state = self.MANUAL_MODE_INITIALIZE
                    continue
        
                if self.vibration_pi.should_start():
                    self.next_state = self.AUTO_MODE_MEASURE
                    continue
        
            elif self.current_state == self.AUTO_MODE_MEASURE:
                self.indicator_lights.busy()
                self.vibration_pi.measurement_sequence_auto()
                self.next_state = self.AUTO_MODE_INITIALIZE
                continue
        
            elif self.current_state == self.MANUAL_MODE_INITIALIZE:
                self.indicator_lights.off()
                self.vibration_pi.update_config(self.config_file_manual)
                self.vibration_pi.batteries.measure()
                self.next_state = self.MANUAL_MODE_WAIT
                continue
        
            elif self.current_state == self.MANUAL_MODE_WAIT:
                self.indicator_lights.ready()
        
                if self.push_button.button_pushed == 2:
                    # log.debug('Would shutdown now. skipped instead')
                    # push_button._button_pushed = 0
                    self.next_state = self.CHARGE_INITIALIZE
                    continue
        
                if self.push_button.button_pushed == 1:
                    # log.debug('Would measure now. skipped instead')
                    # push_button._button_pushed = 0
                    self.next_state = self.MANUAL_MODE_MEASURE
                    continue
        
                if GPIO.input(self.manual_switch_pin) == GPIO.LOW:
                    self.next_state = self.AUTO_MODE_INITIALIZE
                    continue
        
            elif self.current_state == self.MANUAL_MODE_MEASURE:
                self.indicator_lights.busy()
                self.vibration_pi.measurement_sequence_manual()
                self.next_state = self.MANUAL_MODE_WAIT
                continue
        
            elif self.current_state == self.CHARGE_INITIALIZE:
                self.indicator_lights.both()  # potentially replace this with blinking LEDs
                self.switch_state_on_charge_init = GPIO.input(self.manual_switch_pin)
                self.vibration_pi.batteries.charge()
                self.push_button._button_pushed = 0  # This is an ugly hack. The PushButton class should be cleaned up
                self.next_state = self.CHARGE
                continue

            elif self.current_state == self.CHARGE:
                # If long press, shutdown
                if self.push_button.button_pushed == 2:
                    self.next_state = self.SHUTDOWN
                    continue

                # If switch hasn't moved, continue
                if GPIO.input(self.manual_switch_pin) == self.switch_state_on_charge_init:
                    continue

                # If this code is reached, the switch was moved and the FSM should be sent to the relevant state
                if GPIO.input(self.manual_switch_pin) == GPIO.HIGH:
                    self.next_state = self.MANUAL_MODE_INITIALIZE
                    continue

                if GPIO.input(self.manual_switch_pin) == GPIO.LOW:
                    self.next_state = self.AUTO_MODE_INITIALIZE
                    continue

            elif self.current_state == self.SHUTDOWN:
                self.indicator_lights.both()
                os.system('sudo shutdown now')
