class Hat:
    channels = None
    samples_per_channel = None
    scan_rate = None
    address = None
    actual_scan_rate = None
    hat = None
    options = None
    channel_mask = None
    num_channels = None
    status = None
    timeout = 5.0

    def __init__(self, channels=[0], samples_per_channel=1000, scan_rate=100000):
        self.channels = channels
        self.channel_mask = self.chan_list_to_mask(self.channels)
        self.num_channels = len(self.channels)
        self.samples_per_channel = samples_per_channel
        self.scan_rate = scan_rate
        self.options = OptionFlags.DEFAULT

        self.address = self.select_hat_device(HatIDs.MCC_118)
        self.mcc118 = mcc118(self.address)

        print('\nSelected MCC 118 HAT device at address', self.address)

        self.actual_scan_rate = self.mcc118.a_in_scan_actual_rate(self.num_channels, self.scan_rate)

        print('\nMCC 118 continuous scan example')
        print('    Functions demonstrated:')
        print('         mcc118.a_in_scan_start')
        print('         mcc118.a_in_scan_read')
        print('    Channels: ', end='')
        print(', '.join([str(chan) for chan in self.channels]))
        print('    Requested scan rate: ', self.scan_rate)
        print('    Actual scan rate: ', self.actual_scan_rate)
        print('    Samples per channel', self.samples_per_channel)
        print('    Options: ', self.enum_mask_to_string(OptionFlags, self.options))

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

    def select_hat_device(self, filter_by_id):

        selected_hat_address = None

        # Get descriptors for all of the available HAT devices.
        hats = hat_list(filter_by_id=filter_by_id)
        number_of_hats = len(hats)

        # Verify at least one HAT device is detected.
        if number_of_hats < 1:
            raise HatError(0, 'Error: No HAT devices found')
        else:
            selected_hat_address = hats[0].address

        if selected_hat_address is None:
            raise ValueError('Error: Invalid HAT selection')

        return selected_hat_address

    def measurement(self):
        print('Starting measurement scan in background.')
        self.mcc118.a_in_scan_start(self.channel_mask, self.samples_per_channel, self.scan_rate, self.options)
        while (True):
            sleep(1)
            self.status = self.mcc118.a_in_scan_status()
            if not self.status.running:
                print('Measurement finished. Reading data from buffer.')
                break
            elif self.status.hardware_overrun:
                print('Hardware overrun during measurement.')
            elif self.status.buffer_overrun:
                print('Buffer overrun during measurement.')

        data = self.mcc118.a_in_scan_read(-1, self.timeout).data
        print('Data successfully read. Cleaning up buffer.')
        self.mcc118.a_in_scan_cleanup()
        return data
