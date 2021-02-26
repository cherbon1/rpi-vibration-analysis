import time
from daqhats import mcc118

import logging
log = logging.getLogger(__name__)


class Hat:
    timeout = 5.0

    def __init__(self, channels=None, samples_per_channel=1000, sampling_rate=100000):
        if channels is None:
            channels = [0]
        self.channels = channels
        self.channel_mask = self.chan_list_to_mask(self.channels)
        self.num_channels = len(self.channels)
        self.samples_per_channel = samples_per_channel
        self.sampling_rate = sampling_rate
        self.options = 0  # 0 is default
        self.status = None

        self.address = 0  # address of daqhat
        self.mcc118 = mcc118(self.address)

        log.debug('Selected MCC 118 HAT device at address: {}'.format(self.address))
        log.debug('MCC 118 HAT firmware: {}'.format(self.mcc118.firmware_version().version))

        self.actual_sampling_rate = self.mcc118.a_in_scan_actual_rate(self.num_channels, self.sampling_rate)

    def chan_list_to_mask(self, chan_list):
        chan_mask = 0

        for chan in chan_list:
            chan_mask |= 0x01 << chan

        return chan_mask

    def enum_mask_to_string(self, enum_type, bit_mask):
        item_names = []
        if bit_mask == 0:
            item_names.append('DEFAULT')
        for item in enum_type:
            if item & bit_mask:
                item_names.append(item.name)
        return ', '.join(item_names)

    def measurement(self):
        log.debug('Starting measurement scan in background.')
        self.mcc118.a_in_scan_start(self.channel_mask, int(self.samples_per_channel),
                                    int(self.sampling_rate), self.options)
        while True:
            time.sleep(0.2)
            self.status = self.mcc118.a_in_scan_status()
            if not self.status.running:
                log.debug('Measurement finished. Reading data from buffer.')
                break
            elif self.status.hardware_overrun:
                log.warning('Hardware overrun during measurement.')
            elif self.status.buffer_overrun:
                log.warning('Buffer overrun during measurement.')

        data = self.mcc118.a_in_scan_read(-1, self.timeout).data
        log.debug('Data successfully read. Cleaning up buffer.')
        self.mcc118.a_in_scan_cleanup()
        return data


class DummyHat(Hat):
    def __init__(self, channels=None, samples_per_channel=1000, sampling_rate=100000):
        if channels is None:
            channels = [0]
        self.channels = channels
        self.channel_mask = None
        self.num_channels = len(self.channels)
        self.samples_per_channel = samples_per_channel
        self.sampling_rate = sampling_rate
        self.actual_sampling_rate = sampling_rate
        self.address = 'dummy'

    def measurement(self):
        from numpy.random import random
        time.sleep(self.samples_per_channel/self.sampling_rate)
        return 1.1+random(int(self.samples_per_channel))

if __name__ == "__main__":
    # Start logging:
    logging.basicConfig(# filename='/home/pi/Documents/vibration_logger.log',
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    hat = Hat(samples_per_channel=1000*15, sampling_rate=1000)
    print(len(hat.measurement()))