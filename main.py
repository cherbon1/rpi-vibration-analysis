import os
from fsm import VibrationFSM
import RPi.GPIO as GPIO

import logging
log = logging.getLogger(__name__)

if __name__ == "__main__":
    # Ignore GPIO warnings
    GPIO.setwarnings(False)

    # Start logging:
    logging.basicConfig(filename='/home/pi/Documents/vibration_logger.log',
        level=logging.INFO,
        format='%(asctime)s %(message)s')

    # Define config files
    config_file_auto = 'config_d.json'
    config_file_manual = 'config_manual.json'

    config_file_auto_full_path = os.path.join(os.path.dirname(__file__), config_file_auto)
    config_file_manual_full_path = os.path.join(os.path.dirname(__file__), config_file_manual)

    vibration_fsm = VibrationFSM(config_file_auto_full_path, config_file_manual_full_path)

    try:
        vibration_fsm.run()
    except Exception as e:
        vibration_fsm.indicator_lights.both()  # exits with error: both lights on
        raise e

    vibration_fsm.indicator_lights.off()  # exits noramlly: both lights off
