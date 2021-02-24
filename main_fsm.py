# A finite state machine for controlling the raspberry pi vibration control
import RPi.GPIO as GPIO
from push_button import PushButton
from indicator_lights import IndicatorLights
from vibration_station import VibrationPi
import os

config_file_auto = './config_d.json'
config_file_manual = './config_manual.json'

# Setup connection to hardware
push_button = PushButton()
GPIO.add_event_detect(22, GPIO.FALLING, callback=push_button.button_readout, bouncetime=500)

indicator_lights = IndicatorLights(17, 27)

manual_switch_pin = 10

GPIO.setwarnings(False)  # Ignore warning for now
if not (GPIO.getmode() == GPIO.BCM):  # Use BCM numbering
    GPIO.setmode(GPIO.BCM)
GPIO.setup(manual_switch_pin, GPIO.IN,
           pull_up_down=GPIO.PUD_DOWN)


# Define FSM states
class VibrationStationStates:
    AUTO_MODE_INITIALIZE = 0
    AUTO_MODE_WAIT = 1
    AUTO_MODE_MEASURE = 2

    MANUAL_MODE_INITIALIZE = 3
    MANUAL_MODE_WAIT = 4
    MANUAL_MODE_MEASURE = 5

    SHUTDOWN = 9


# FSM initialization and running
next_state = VibrationStationStates.AUTO_MODE_INITIALIZE

while True:
    # What state did we just transition to?
    current_state = next_state

    # What needs to be done in current state
    if current_state == VibrationStationStates.AUTO_MODE_INITIALIZE:
        indicator_lights.off()
        vibration_pi = VibrationPi(config_file_auto)

        next_state = VibrationStationStates.AUTO_MODE_WAIT
        continue

    elif current_state == VibrationStationStates.AUTO_MODE_WAIT:
        indicator_lights.ready()

        if push_button.button_pushed == 2:
            next_state = VibrationStationStates.SHUTDOWN
            continue

        if GPIO.input(manual_switch_pin) == GPIO.HIGH:
            next_state = VibrationStationStates.MANUAL_MODE_INITIALIZE
            continue

        if vibration_pi.should_start():
            next_state = VibrationStationStates.AUTO_MODE_MEASURE
            continue

    elif current_state == VibrationStationStates.AUTO_MODE_MEASURE:
        indicator_lights.busy()
        vibration_pi.measurement_sequence_auto()
        next_state = VibrationStationStates.AUTO_MODE_INITIALIZE
        continue

    elif current_state == VibrationStationStates.MANUAL_MODE_INITIALIZE:
        indicator_lights.off()
        vibration_pi.update_config(config_file_manual)
        vibration_pi.batteries.measure()
        next_state = VibrationStationStates.MANUAL_MODE_WAIT
        continue

    elif current_state == VibrationStationStates.MANUAL_MODE_WAIT:
        indicator_lights.ready()

        if push_button.button_pushed == 2:
            next_state = VibrationStationStates.SHUTDOWN
            continue

        if push_button.button_pushed == 1:
            next_state = VibrationStationStates.MANUAL_MODE_MEASURE
            continue

        if GPIO.input(manual_switch_pin) == GPIO.LOW:
            next_state = VibrationStationStates.AUTO_MODE_INITIALIZE
            continue

    elif current_state == VibrationStationStates.MANUAL_MODE_MEASURE:
        indicator_lights.busy()
        vibration_pi.measurement_sequence_manual()
        next_state = VibrationStationStates.MANUAL_MODE_WAIT
        continue

    elif current_state == VibrationStationStates.SHUTDOWN:
        indicator_lights.both()
        os.system('sudo shutdown now')
