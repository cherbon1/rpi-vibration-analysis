# A finite state machine for controlling the raspberry pi vibration control
import RPi.GPIO as GPIO
from push_button import PushButton
from indicator_lights import IndicatorLights
from vibration_station import VibrationPi
import time

import logging
log = logging.getLogger(__name__)

# Define config files
config_file_auto = './config_d.json'
config_file_manual = './config_manual.json'

# Setup connection to hardware
if not (GPIO.getmode() == GPIO.BCM):  # Use BCM numbering
    GPIO.setmode(GPIO.BCM)

indicator_lights = IndicatorLights(17, 27)

push_button = PushButton()
push_button_pin = 22
GPIO.setup(push_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(push_button_pin, GPIO.FALLING, callback=push_button.button_readout, bouncetime=500)

manual_switch_pin = 10
# GPIO.setwarnings(False)  # Ignore warning for now
GPIO.setup(manual_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Start logging:
logging.basicConfig(filename='/home/pi/Documents/vibration_logger.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

vibration_pi = VibrationPi(config_file_auto)

vibration_pi.batteries.charge()
time.sleep(1)
vibration_pi.batteries.measure()
time.sleep(1)
vibration_pi.hat.samples_per_channel(100)
print(vibration_pi.hat.measurement())
