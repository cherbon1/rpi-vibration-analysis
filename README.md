# rpi-vibration-analysis

RaspberryPi powered automatic vibration monitoring station.

To-do / potential improvements:
- Troubleshoot/fix/test writing to influxDB.
- Better handling of lack of connection to network (e.g. blink LEDs to signal it, then record locally in manual mode)
- Read config files off of Cerberous --> more straightforward way to change settings (Requires everyone to have write access to Cerberous)

## Vibration monitoring station: Instructions

### Configuration of measurements
1. Connect to Cerberous
2. In the folder /BuildingVibrations/config, you'll find 4 .json files with configuration parameters. These files
contain the settings for the manual and auto modes of both stations. Edit whichever config file you want to match your
desired settings

Note: it is important that the station be connected to the network when starting up. If that's not the case, the station
will be unable to read the config file on Cerberous, and will default to locally stored parameters instead.

### Automated measurements of building vibrations at regular intervals
1.	Connect the station to power and to the network
2.	Verify that the accelerometer settings are correct: On, 450Hz, 1000V/g
3.	Set the control switch to Auto. One LED should be on at all times. If either both or neither are on, something's wrong.

### Manual measurements using the built-in DAQ
1.	Connect the station to power and to the network
2.	Verify that the accelerometer settings are correct: On, 450Hz, 1000V/g
3.	Set the control switch to Manual. One LED should be on at all times. If either both or neither are on, something's wrong
4.	Press the Record button to launch a measurement using the settings found in config_manual.json (See section below on how to edit settings)
5.	When you’re done, turn off the accelerometer (switch to off) and shutdown the station (see below)
6.	Your measurements can be found on Cerberous, in the folder /BuildingVibrations/custom

### Manual measurements using an external DAQ
1.	Shutdown the station (see below)
2.	Disconnect the station from power and network
3.	Choose your accelerometer settings on the front panel
4.	Use the BNC output at the back of the station to connect your DAQ

###Changing the measurement settings (now obsolete. See Configuration of Measurements above instead)
1.	Connect the station to power and to the network
2.	Connect to the raspberry pi remotely (via SSH or VNC)
3.	Open the corresponding config file in your favorite text editor adjust your settings and save the file
4.	Toggle the Manual/Auto switch to make sure the new settings have been read

The config files are located in the following locations
For automatic measurements:
`/home/pi/Documents/rpi-vibration-analysis/config_d.json`
`/home/pi/Documents/rpi-vibration-analysis/config_m.json`

For manual measurements:
`/home/pi/Documents/rpi-vibration-analysis/config_manual.json`

For manual measurements, you’ll typically want to change `filename`, `settling_time`,
`measurement_time` and `sampling_rate`.  
`filename`: name of saved file  
`settling_time`: time between button press and start of data acquisition in minutes. (Typically 0 for manual measurements)  
`measurement_time`: Duration of measurement in minutes  
`sampling_rate`: Sampling rate in samples per second (Typically 1000)  

### Charging the batteries
If the batteries ever get completely discharged, you may want to recharge them without ever measuring. When the station
is in the Ready state, press and hold the record button for 2 seconds to put the station into a charging state.
Both LEDs should turn on. In this state, the batteries are constantly connected to the charger. To exit this state, 
simply flip the manual/auto switch to go back to the corresponding mode.  
Note that under normal operation, this charging mode shouldn't be necessary.

### Shutting down the station
When the station is in the Ready state, press and hold the record button for 2 seconds to put the station into
it's charging state. Press and hold the button for 2 seconds again to shut down the station.
Alternatively, connect to the station via SSH, and shut down with 
sudo shutdown now

### Other things you may want to do:
#### Connect to station remotely
Connect to the station via SSH (e.g. ssh pi@raspberry-pi-02.ee.ethz.ch in a terminal) or via VNC Viewer
(free app from RealVNC). 
The log-in details are listed on the group OneNote.

#### Verify the status of the python program
1.	Connect to station remotely
2.	In a terminal, type in the command: service vibration-logging status

#### Verify the logs
1.	Connect to station remotely
2.	In a terminal, type in the command: tail -f ./Documents/vibration-logger.log

#### Use different config files
1.	Connect to station remotely
2.	Edit the config file names (config_file_auto or config_file_manual) in /home/pi/Documents/rpi-vibration-analysis/main.py

### Other notes
Requires: [daqhats](https://github.com/mccdaq/daqhats),
[influxdb-client-python](https://github.com/influxdata/influxdb-client-python), and the usual
suspects (`numpy`, `h5py`, `scipy`, `pandas`)