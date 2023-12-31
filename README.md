# rpi-vibration-analysis

RaspberryPi powered automatic vibration monitoring station.

To-do:
- Troubleshoot/fix/test writing to influxDB.
- Consider changing the service to restart automatically on failure with `Restart=always`, see [here](https://serverfault.com/questions/252137/how-to-automatically-restart-a-service-on-failure-in-linux)

## Vibration monitoring station: Instructions
![vibration station control panels](VibrationStation.jpg)

### Configuration files and output files
The vibration station loads its measurement parameters from config files stored on Cerberous, a network file storage system hosted in our lab. The recorded data is saved to Cerberous as well. Therefore, if you want to use the built-in DAQ to measure data, **it is imperative that the vibration station has a conenction to the network.**

#### Connecting to Cerberous
In your file explorer of choice, connect to `cerberous.ee.ethz.ch`. The vibration data is stored in the subfolder `BuildingVibration`. By default, members of our group have read-only access to this folder. If you need write access, e.g. to modify a config file, you should connect with the `vibrationLogger` credentials. The corresponding password can be found in our group OneNote. (This repository is public, I don't want to share the password here)

#### File structure of Cerberous
The `BuildingVibration` folder contains 4 main subfolders:
- `config` contains the configuration files for the measurement parameters
- `d` and `m` contain the automated measurement data done by the D-floor station and M-floor station respectively
- `custom` contains manual measurement data

### Configuration of measurements
If you want to modify the configuration of a measurement, connect to Cerberous and edit the corresponding file in the `config` folder (auto/manual measurements, d/m floor station). Then, toggle the `Auto`/`Manual` switch. This prompts the vibration station to reload its settings from Cerberous. 

Once again, **the station must be connected to the network** or else it won't be able to read the config files from or save data to Cerberous.

Most fields to be edited are self-explanatory. The measurement related ones are:
- `measurement_time`: duration of measurement in minutes
- `settling_time`: time to wait between button press and start of measurement (mainly relevant for automatic measurements, where the pre-amp needs some time to settle)
- `sampling_rate`: sampling rate of DAQ in Hz. Going beyond 1000Hz doesn't make much sense since the amplifier low-pass filters at 450Hz.
If you want to restore a file to its default state, simply copy the corresponding config file in this repository.
- `measurement_period`: Time between measurements. Only applies to automatic measurements. 

### Automated measurements of building vibrations at regular intervals
1.	Connect the station to power and to the network
2.	Verify that the accelerometer settings are correct: `On`, `450Hz`, `1000V/g`
3.	Set the control switch to `Auto` (top position). One LED should be on at all times. If either both or neither are on, something's wrong.

### Manual measurements using the built-in DAQ
1.	Connect the station to power and to the network
2.	Verify that the accelerometer settings are correct: `On`, `450Hz`, `1000V/g`
3.	Set the control switch to `Manual`. One LED should be on at all times. If either both or neither are on, something's wrong
4.	Press the Record button to launch a measurement using the settings found in `config_manual.json` (See section [Configuration of Measurements](#Configuration-of-measurements) on how to edit settings)
5.	When you’re done, turn off the accelerometer (switch to off) and shutdown the station (see below)
6.	Your measurements can be found on Cerberous, in the folder `/BuildingVibrations/custom`, with the filename specified in `config_manual.json`

### Manual measurements using an external DAQ
1.	Shutdown the station (see below)
2.	Disconnect the station from power and network
3.	Choose your accelerometer settings on the front panel
4.	Use the BNC output at the back of the station to connect your DAQ

### Charging the batteries
If the batteries ever get completely discharged, you may want to recharge them without ever measuring. When the station
is in the `Ready` state, press and hold the record button for 2 seconds to put the station into a charging state.
Both LEDs should turn on. In this state, the batteries are constantly connected to the charger. To exit this state, 
toggle the `Auto`/`Manual` switch.  
Note that under normal operation, this charging mode shouldn't be necessary.

### Shutting down the station
When the station is in the `Ready` state, press and hold the record button for 2 seconds to put the station into
its charging state. Press and hold the button for 2 seconds again to shut down the station.
Alternatively, connect to the station via SSH, and shut down with 
sudo shutdown now

### Other things you may want to do:
#### Interrupt a measurement
There's currently no simple way to do that. If you really care about interrupting a measurement, you should connect to the station remotely, and restart the `vibration-logging` service by running `sudo service vibration-logging restart` in a terminal


#### Connect to station remotely
Connect to the station via SSH (e.g. `ssh pi@raspberry-pi-02.ee.ethz.ch` in a terminal) or via VNC Viewer
(free app from RealVNC). 
The log-in details are listed on the group OneNote.

#### Verify the status of the python program
1.	Connect to station remotely
2.	In a terminal, type in the command: `service vibration-logging status`

#### Verify the logs
1.	Connect to station remotely
2.	In a terminal, type in the command: `tail -f ./Documents/vibration-logger.log`

#### Use different config files
1.	Connect to station remotely
2.	Edit the config file names (`config_file_auto` or `config_file_manual`) in `/home/pi/Documents/rpi-vibration-analysis/main.py`

### Other notes
Requires: [daqhats](https://github.com/mccdaq/daqhats),
[influxdb-client-python](https://github.com/influxdata/influxdb-client-python), and the usual
suspects (`numpy`, `h5py`, `scipy`, `pandas`)

### Installing this on a new raspberry pi
1. Clone this repo somewhere on the raspberry pi's home directory
2. Create a service file in `/lib/systemd/system/vibration-logging.service` with the following contents:
```buildoutcfg
[Unit]
Description=Logs building vibration to cerberous.
After=multi-user.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 /home/pi/Documents/rpi-vibration-analysis/main.py
Restart=on-abort

[Install]
WantedBy=multi-user.target

```

3. Enable the service so that it starts automatically at boot with `systemctl enable vibration-logging`