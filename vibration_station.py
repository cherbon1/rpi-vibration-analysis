import time
from datetime import datetime, timedelta
import os
import h5py
import json
from influxdb_client import InfluxDBClient
import batteries
import daq_hat
import numpy as np
import pandas as pd
from derive_psd import derive_psd, integrate_peaks
from cerberous_connection import CerberousConnection

import logging
log = logging.getLogger(__name__)

class VibrationPi:
    '''
    Class that handle the Raspberry Pi tunring on and doing its shit.
    Has:
    batteries, daqhat, measurement queue
    notion of where to write to
    knows how to do an fft
    reads a json file with config at startup.
    '''
    def __init__(self, config):
        '''
        :param config: dict or filepath containing json file. Contains settings for saving data, ...
        '''

        # read config file
        self.update_config(config)

    def update_config(self, config):
        '''
        Reads a config file, and updates VibrationPi's settings accordingly
        Parameters
        ----------
        config

        Returns
        -------

        '''
        # Read config params
        if type(config) is dict:
            self.config = config
        else:
            with open(config, 'r') as f:
                self.config = json.load(f)

        # General config
        self.location = self.config.get('location', 'HPP')  # 'D' or 'M'
        self.write_to = self.config.get('write_to', 'h5py')  # whether to write to InfluxDB or h5py or both

        # measurement related config
        self.sampling_rate = self.config.get('sampling_rate', 1000.0)  # DAQ sampling rate
        self.settling_time = self.config.get('settling_time', 5.0)  # settling time in minutes
        self.measurement_duration = self.config.get('measurement_time', 10.0)  # duration of the minutes
        self.measurement_period = self.config.get('measurement_period', 30.0)  # time between measurements in mins
        if self.measurement_period > 60.0:
            log.warning('Desired period too long, reduced to 60.0')
            self.measurement_period = 60.0
        if self.measurement_duration + self.settling_time > self.measurement_period:
            log.warning('Measurements too frequent, some will be skipped')

        # spectrum related parameters
        self.subdivision_factor = self.config.get('subdivision_factor', 32)  # 32 is fitting for 5 min measurements

        # InfluxDB related parameters
        if self.write_to in ['InfluxDB', 'both']:
            self.analysis_windows = self.config['analysis_windows']  # no default value here
            self.token = self.config['token']
            self.org = self.config.get('org', 'PhotonicsVibration')
            self.time_trace_bucket = self.config.get('time_trace_bucket', 'TimeTraceData')
            self.spectrum_bucket = self.config.get('spectrum_bucket', 'SpectrumData')
            self.peaks_bucket = self.config.get('peaks_bucket', 'IntegratedPeaksData')
            self.url = self.config.get('url', 'http://129.132.1.229:8086')

        # Cerberous related parameters
        if self.write_to in ['h5py', 'both']:
            self.filename = self.config.get('filename', 'default')
            self.network_drive = self.config.get('network_drive', '/media/vibration')
            self.save_location = self.config.get('save_location', '/media/vibration/d')
            self.temp_save_location = self.config.get('temp_save_location', '/home/pi/Documents/temp_file_storage')

        # Initialize timing
        self.update_next_start_time()

        # Check that the external connections are running
        if self.write_to in ['InfluxDB', 'both']:
            self.open_influx_client()  # defines self.client and self.write_api attributes
            # (I don't think it's harmful to call this is client is already open)

        if self.write_to in ['h5py', 'both']:
            self.cerberous = CerberousConnection(self.network_drive, retries=2)
            # (I don't think it's harmful to call this is CerberousConnection is already open)

        # initialize batteries and hat (needs to be done after reading config file, b.c. hat needs meas. duration info)
        self.batteries = batteries.Batteries()
        self.hat = daq_hat.Hat(channels=[0],
                               samples_per_channel=self.sampling_rate * self.measurement_duration * 60.0,
                               sampling_rate=self.sampling_rate)

    def open_influx_client(self):
        self.client = InfluxDBClient(url=self.url, token=self.token)
        self.write_api = self.client.write_api()

    def update_next_start_time(self):
        '''
        Sets next_start_time to the minutes at which the next measurement sequence should start
        '''
        current_time = datetime.now()
        # Number of minutes after the current hour that the next measurement should take place
        next_minute = ((current_time + timedelta(minutes=self.settling_time)).timetuple().tm_min //
                       self.measurement_period + 1) * self.measurement_period

        # datetime object of when the next measurement should take place
        self.next_start_time = (current_time + timedelta(hours=next_minute // 60)) \
            .replace(minute=int(next_minute % 60), second=0, microsecond=0)

    def should_start(self):
        '''Returns True if it's time for an automated measurement to be launched'''
        return datetime.now() + timedelta(minutes=self.settling_time) >= self.next_start_time

    def measurement_sequence(self):
        time.sleep(self.settling_time * 60.0)
        timestamp = datetime.now()
        data = self.hat.measurement()
        return data, timestamp

    def measurement_sequence_auto(self):
        '''Measurement sequence with battery handling and some extra checks to counter for errors'''
        measurement_done = False
        retries = 10
        while not measurement_done:
            try:
                self.batteries.measure()
                data, timestamp = self.measurement_sequence()
                self.batteries.charge()
                measurement_done = True
            except Exception as e:
                retries -= 1
                if not retries:
                    log.warning('Measurement failed too often, rebooting system')
                    time.sleep(10)
                    os.system('reboot')
                log.warning('{} during measurement, retrying'.format(e))
                time.sleep(60)
                self.__init__(self.config)

        self.save_data(data, timestamp)

    def measurement_sequence_manual(self):
        '''Make sure batteries are connected before launching this'''
        data, timestamp = self.measurement_sequence()
        self.save_data(data, timestamp)

    def save_data(self, data, timestamp):
        if self.write_to in ['InfluxDB', 'both']:
            # open connection to server
            # (I don't think it hurts to repeat this, but weirdness can happen it it's  been open for too long)
            log.debug('Opening connection to Influx')
            self.open_influx_client()

            # # Write time-traces to time_trace_bucket
            # log.debug('Start writing traces...')
            # self.write_time_trace_to_influx(data, timestamp)
            # log.debug('Done.')

            # calculate psd, and write psd to spectrum_bucket
            log.debug('Computing PSDs...')
            frequency, spectrum = derive_psd(data, self.hat.sampling_rate, method='welch',
                                             subdivision_factor=self.subdivision_factor)
            clip = 2  # drop DC part of spectrum
            log.debug('Done.')
            log.debug('Start writing PSDs...')
            self.write_spectrum_to_influx(frequency[clip:], spectrum[clip:], timestamp)
            log.debug('Done.')

            # integrate peaks and write to peaks_bucket
            log.debug('Compute integrated peaks...')
            integrated_peaks = integrate_peaks(frequency, spectrum, self.analysis_windows)
            log.debug('Done.')
            log.debug('Write peaks...')
            self.write_peak_data_to_influx(integrated_peaks, timestamp)
            log.debug('Done.')

        elif self.write_to in ['h5py', 'both']:
            try:
                self.cerberous.mount_network_drive()
                save_to = self.save_location
            except RuntimeError:
                log.warning('Connection to network drive failed, data will be saved locally')
                save_to = self.temp_save_location

            filename = timestamp.strftime('%Y-%m') + '.h5' if self.filename == 'default' else self.filename
            save_to = os.path.join(save_to, filename)

            with h5py.File(save_to, 'a') as f:
                group = timestamp.strftime('%Y-%m-%d')
                if group not in f:
                    f.create_group(group)

                dset_name = timestamp.strftime('%H-%M')
                dset = f[group].create_dataset(dset_name, data=data)
                dset.attrs['channels'] = self.hat.channels
                dset.attrs['samples_per_channel'] = self.hat.samples_per_channel
                dset.attrs['sampling_rate'] = self.hat.sampling_rate
                dset.attrs['address'] = self.hat.address
                dset.attrs['actual_sampling_rate'] = self.hat.actual_sampling_rate
                dset.attrs['timestamp'] = timestamp.strftime('%Y-%m-%d:%H-%M-%S')

            # if there are any temporary data files, merge them with the main one.
            self.merge_hdf_files()

        else:
            raise ValueError('Unknown saving method {}'.format(self.write_to))

    def write_time_trace_to_influx(self, data, timestamp):
        # get timestamp array in ns (do this before pd.Dataframe to avoid issues with DST)
        start_timestamp = timestamp.timestamp() * 1e9
        step = 1e9 / self.hat.actual_sampling_rate
        timestamps = np.arange(len(data)) * step + start_timestamp
        timestamps = timestamps.astype(int)

        # Make string tags to simplify splitting apart measurements when querying data
        time_str = timestamp.strftime('%H-%M')
        date_str = timestamp.strftime('%Y-%m-%d')

        # Build DataFrame
        df = pd.DataFrame({'time':timestamps, 'sensor_output':data,
                          'date_string':date_str, 'time_string':time_str, 'location':self.location})
        df.set_index('time', inplace=True)

        # Upload DataFrame
        self.write_api.write(bucket=self.time_trace_bucket, org=self.org, record=df,
                             data_frame_measurement_name='accelerometer_data',
                             data_frame_tag_columns=['date_string', 'time_string', 'location'])

    def write_spectrum_to_influx(self, frequency, spectrum, timestamp):
        # Since Influx is for time-series measurements, store frequency axis as time.
        # get timestamp array in ns (from frequency)
        seconds_to_Hz = np.max(frequency) / (self.measurement_duration * 60.0)  # conversion factor
        start_timestamp = timestamp.timestamp() * 1e9
        timestamps = frequency * 1e9 / seconds_to_Hz + start_timestamp
        timestamps = timestamps.astype(int)

        # Make string tags to simplify splitting apart measurements when querying data
        time_str = timestamp.strftime('%H-%M')
        date_str = timestamp.strftime('%Y-%m-%d')

        # Build DataFrame
        df = pd.DataFrame({'time': timestamps, 'spectrum': spectrum, 'seconds_to_Hz':seconds_to_Hz,
                           'date_string': date_str, 'time_string': time_str, 'location': self.location})
        df.set_index('time', inplace=True)

        # Upload DataFrame
        self.write_api.write(bucket=self.spectrum_bucket, org=self.org, record=df,
                             data_frame_measurement_name='spectrum_data',
                             data_frame_tag_columns=['date_string', 'time_string', 'location', 'seconds_to_Hz'])

    def write_peak_data_to_influx(self, integrated_peaks, timestamp):
        timestamp = int(timestamp.timestamp() * 1e9)

        integrated_peaks = {str(k): v for k, v in integrated_peaks.items()}
        df = pd.DataFrame({'time': timestamp, 'location': self.location, **integrated_peaks}, index=[0])
        df.set_index('time', inplace=True)

        # Upload DataFrame
        self.write_api.write(bucket=self.peaks_bucket, org=self.org, record=df,
                             data_frame_measurement_name='integrated_peaks',
                             data_frame_tag_columns=['location'])

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

