class VibrationPi:
    batteries = None
    hat = None
    data = None
    timestamp = time()
    save_location = '/media/vibration/d'
    temp_save_location = '/home/pi/Documents/temp_file_storage'
    reinit_counter = 0
    log_level = logging.DEBUG
    log_location = '/home/pi/Documents'

    def __init__(self, channels=[0], samples_per_channel=1000, scan_rate=100000):
        logging.basicConfig(filename=os.path.join(self.log_location, 'vibration_logger.log'),
                            level=self.log_level,
                            format='%(asctime)s %(message)s')
        self.batteries = Batteries()

        for i in range(10):
            if self.server_connection:
                break
            sleep(10)
        self.mount_network_drive()
        self.hat = Hat(channels, samples_per_channel, scan_rate)

    @property
    def network_drive_mounted(self):
        mounts = subprocess.check_output('mount').split(b'\n')
        contains_vibration = any([b'vibration' in m for m in mounts])
        return contains_vibration

    def mount_network_drive(self):
        if not self.network_drive_mounted:
            logging.debug('Network storage was not mounted.')
            os.system('mount /media/vibration')
            if not self.network_drive_mounted:
                logging.debug('Network storage mount failed.')
            else:
                logging.debug('Network storage was mounted.')
        else:
            logging.debug('Network was already mounted.')

    def save_data(self):
        if not self.network_drive_mounted:
            self.mount_network_drive()
        if self.network_drive_mounted:
            with h5py.File(os.path.join(self.save_location, self.ts_month + '.h5'), 'a') as h5_file:
                ts_date = self.ts_date
                if ts_date not in h5_file:
                    h5_file.create_group(ts_date)

                ds = h5_file[ts_date].create_dataset(self.ts_minute, data=self.data)
                ds.attrs['channels'] = self.hat.channels
                ds.attrs['samples_per_channel'] = self.hat.samples_per_channel
                ds.attrs['scan_rate'] = self.hat.scan_rate
                ds.attrs['address'] = self.hat.address
                ds.attrs['actual_scan_rate'] = self.hat.actual_scan_rate
                ds.attrs['timestamp'] = self.ts_datetime

            # if there are any temporary data files, merge them with the main one.
            self.merge_hdf_files()


        else:
            logging.debug('Connection to server timed out. Data saved locally instead.')

            with h5py.File(os.path.join(self.temp_save_location, self.ts_month + '.h5'), 'a') as h5_file:
                ts_date = self.ts_date
                if ts_date not in h5_file:
                    h5_file.create_group(ts_date)

                ds = h5_file[ts_date].create_dataset(self.ts_minute, data=self.data)
                ds.attrs['channels'] = self.hat.channels
                ds.attrs['samples_per_channel'] = self.hat.samples_per_channel
                ds.attrs['scan_rate'] = self.hat.scan_rate
                ds.attrs['address'] = self.hat.address
                ds.attrs['actual_scan_rate'] = self.hat.actual_scan_rate
                ds.attrs['timestamp'] = self.ts_datetime
            # raise ConnectionError('Connection to server timed out. Couldn\'t save data.')

    @property
    def ts_date(self):
        return dt.fromtimestamp(self.timestamp).strftime('%Y-%m-%d')

    @property
    def ts_month(self):
        return dt.fromtimestamp(self.timestamp).strftime('%Y-%m')

    @property
    def ts_minute(self):
        return dt.fromtimestamp(self.timestamp).strftime('%H-%M')

    @property
    def ts_time(self):
        return dt.fromtimestamp(self.timestamp).strftime('%H-%M-%S')

    @property
    def ts_datetime(self):
        return dt.fromtimestamp(self.timestamp).strftime('%Y-%m-%d:%H-%M-%S')

    def merge_hdf_files(self):
        # Check if any files need to be merged
        file_list = os.listdir(self.temp_save_location)
        file_list = list(filter(lambda x: x.endswith('.h5'), file_list))
        file_list.sort()
        for temp_file in file_list:
            # open both files simultaneously
            with h5py.File(os.path.join(self.temp_save_location, temp_file), 'r') as h5_temp_file, \
                    h5py.File(os.path.join(self.save_location, temp_file), 'a') as h5_file:

                # for each date in the temp file
                for temp_date_group in h5_temp_file:

                    # create the group if necessary
                    if temp_date_group not in h5_file:
                        h5_file.create_group(temp_date_group)

                    # copy each dataset over
                    for dataset in h5_temp_file[temp_date_group]:

                        try:
                            # get data
                            data = h5_temp_file[temp_date_group][dataset]
                            # create new dataset
                            ds = h5_file[temp_date_group].create_dataset(dataset, data=data)
                            # copy all attributes
                            for attr in h5_temp_file[temp_date_group][dataset].attrs:
                                ds.attrs[attr] = h5_temp_file[temp_date_group][dataset].attrs[attr]
                        except RuntimeError:
                            logging.debug('Dataset ' + dataset + ' already exists')
            # delete temporary file
            os.remove(os.path.join(self.temp_save_location, temp_file))
            logging.debug('File ' + temp_file + ' has been removed')

    def measurements_sequence(self, t_wait_meas=0):
        t_wait_meas_0 = 60 * t_wait_meas
        while (True):
            try:
                #                # typical settings
                #                self.wait_full_hour()

                # measure often
                self.wait_n_mins(10)

                self.batteries.measure()
                sleep(t_wait_meas_0)
                self.timestamp = time()
                self.data = self.hat.measurement()
                self.batteries.charge()
                self.save_data()
            except:
                self.reinit_counter += 1
                if self.reinit_counter < 10:
                    logging.debug('Failed during measurement sequence. Try to reinitialize after waiting for 60s.')
                    sleep(60)
                    self.__init__(channels=self.hat.channels,
                                  samples_per_channel=self.hat.samples_per_channel,
                                  scan_rate=self.hat.scan_rate)
                    self.measurements_sequence(t_wait_meas)
                else:
                    logging.debug(
                        'Failed during measurement sequence for more then 10 times. Try rebooting device in 10s.')
                    sleep(10)
                    os.system('reboot')

    @property
    def server_connection(self):
        ret_val = os.system('ping -c 1 cerberous > /dev/null')
        if ret_val == 0:
            return True
        else:
            return False

    def wait_full_hour(self):
        t_now = int(dt.fromtimestamp(time()).strftime('%M'))
        t_delta_full = abs(50 - t_now)
        while (t_delta_full > 1):
            t_now = int(dt.fromtimestamp(time()).strftime('%M'))
            t_delta_full = abs(50 - t_now)
            sleep(10)
        return

    def wait_n_mins(self, n=10):
        """ Waits until the next n minutes mark (defaults to 10)"""
        t_now = int(dt.fromtimestamp(time()).strftime('%M'))
        while bool(t_now % n):  # repeat while t_now is not a multiple of n
            t_now = int(dt.fromtimestamp(time()).strftime('%M'))
            sleep(10)
        return


if __name__ == '__main__':
    # Careful, must also toggle comments in measurements_sequence above!!!

    #    # Typical settings (run once per hour, for 5 mins, wait 10 mins before measurement)
    #    V = VibrationPi(samples_per_channel=300000, scan_rate=1000)
    #    V.measurements_sequence(t_wait_meas=10)

    # Measure often (run once every 10 mins, for 3 mins, wait 4 mins before measurement)
    V = VibrationPi(samples_per_channel=180000, scan_rate=1000)
    V.measurements_sequence(t_wait_meas=4)
