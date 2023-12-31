import time
import subprocess
import os

import logging
log = logging.getLogger(__name__)


class CerberousConnection:
    def __init__(self, network_drive_location, connect=True, retries=2):
        self.network_drive_location = network_drive_location
        self.retries = retries
        if connect:
            self.connect_to_server()

    def connect_to_server(self):
        retries = self.retries
        return_val = os.system('ping -c 1 cerberous > /dev/null')  # returns 0 if success, 256 if fail
        while return_val:
            log.warning('Connection to cerberous failed, will try again')
            retries -= 1
            if not retries:
                raise RuntimeError('Failed to connect to cerberous')
            self.mount_network_drive()
            time.sleep(5)

    @staticmethod
    def check_connection():
        mounts = subprocess.check_output('mount').split(b'\n')
        return any([b'vibration' in m for m in mounts])

    def mount_network_drive(self):
        if self.check_connection():
            log.debug('Network storage is already available')
            return
        # Mount the drive
        os.system('mount {}'.format(self.network_drive_location))

        # Check that it was successfully mounted
        retries = self.retries
        while not self.check_connection():
            log.warning('Network storage was not mounted, will try again')
            time.sleep(2)
            os.system('mount {}'.format(self.network_drive_location))
            retries -= 1
            if not retries:
                raise RuntimeError('Failed to mount network drive')

class DummyCerberousConnection(CerberousConnection):
    @staticmethod
    def connect_to_server():
        return

    @staticmethod
    def check_connection():
        return True
