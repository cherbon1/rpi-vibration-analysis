import os
from fsm import VibrationFSM
import RPi.GPIO as GPIO
from cerberous_connection import CerberousConnection

import logging
log = logging.getLogger(__name__)

if __name__ == "__main__":
    # Ignore GPIO warnings
    GPIO.setwarnings(False)

    # Check connection to cerberous
    try:
        cerberous_conn = CerberousConnection('/media/vibration')
        cerberous_conn.mount_network_drive()
    except RuntimeError:
        log.exception('Cerberous connection failed')
        pass

    # Start logging:
    logging.basicConfig(filename='/home/pi/Documents/vibration_logger.log',
        level=logging.INFO,
        format='%(asctime)s %(message)s')

    # Define config file names
    config_file_auto_name = 'config_auto_d.json'
    config_file_manual_name = 'config_manual_d.json'

    # Define remote location and filenames
    config_file_directory_remote = '/media/vibration/config/'
    config_file_auto_remote = os.path.join(config_file_directory_remote, config_file_auto_name)
    config_file_manual_remote = os.path.join(config_file_directory_remote, config_file_manual_name)

    if os.path.exists(config_file_auto_remote) and \
       os.path.exists(config_file_manual_remote):
        config_file_auto = config_file_auto_remote
        config_file_manual = config_file_manual_remote
    else:
        config_file_auto = os.path.join(os.path.dirname(__file__), config_file_auto_name)
        config_file_manual = os.path.join(os.path.dirname(__file__), config_file_manual_name)

    log.info('Using the following config files:')
    log.info('  Auto: {}'.format(config_file_auto))
    log.info('  Manual: {}'.format(config_file_manual))
    vibration_fsm = VibrationFSM(config_file_auto, config_file_manual)

    try:
        vibration_fsm.run()
    except Exception as e:
        vibration_fsm.indicator_lights.both()  # exits with error: both lights on
        vibration_fsm.vibration_pi.batteries.charge()  # Put batteries into charging mode
        log.exception('VibrationFSM failed')
        raise e

    vibration_fsm.indicator_lights.off()  # exits normally: both lights off
