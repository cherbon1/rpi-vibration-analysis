import os
from fsm import VibrationFSM

import logging
log = logging.getLogger(__name__)

# TODO: Add options for naming datasets etc...
# TODO: Clean up main. Make the FSM its own class
# TODO: make sure shutdown actually shuts down

if __name__ == "__main__":
    # Define config files
    config_file_auto = 'config_d.json'
    config_file_manual = 'config_manual.json'

    config_file_auto_full_path = os.path.join(__file__, config_file_auto)
    config_file_manual_full_path = os.path.join(__file__, config_file_manual)

    vibration_fsm = VibrationFSM(config_file_auto_full_path, config_file_manual_full_path)

    try:
        vibration_fsm.run()
    except Exception as e:
        vibration_fsm.indicator_lights.both()
        raise e
