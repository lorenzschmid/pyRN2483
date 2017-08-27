# RN2483

Small Python library to interface the RN2483 LoRa module over a serial connection. Once connected, the library allows to receive and transmit data over LoRa directly with the module. Supports micropython and desktop machines.

## Command Line Interface

Comes with a command line interface which works as following:

    usage: rn2483 [-h] [-d] [-t TRANSMIT] [-r RECEIVE] [-p PORT]

    Receive and transmit data via rn2483 module.

    optional arguments:
      -h, --help            show this help message and exit
      -d, --debug           Debug mode
      -t TRANSMIT, --transmit TRANSMIT
                            Data to transmit
      -r RECEIVE, --receive RECEIVE
                            Timeout upon reception (in ms)
      -p PORT, --port PORT  Serial Port e.g. pyb, ttyUSB1,
                            /dev/tty.usbserial-A5046HZ5