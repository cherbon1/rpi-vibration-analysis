# rpi-vibration-analysis

Vibration analysis with raspberry pi

Need to install [daqhats](https://github.com/mccdaq/daqhats):

`pip3 install git+https://github.com/mccdaq/daqhats`

Note on recorded times:
Currently, recording times happen on the hour, and every period after the hour.
This means, that a period shorter than 60.0 minutes is not possible.
I could change this by making the system record at midnight, and
every period after that. That would make the minimum period be 1 day.
I don't think it's worth the effort right now.