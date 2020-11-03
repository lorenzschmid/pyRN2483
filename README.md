# RN2483

Small Python library to interface the RN2483 ([Data-Sheet](http://ww1.microchip.com/downloads/en/DeviceDoc/RN2483-Data-Sheet-DS50002346E.pdf), [User-Guide](http://ww1.microchip.com/downloads/en/DeviceDoc/RN2483-LoRa-Technology-Module-Command-Reference-User-Guide-DS40001784G.pdf)) LoRa module over a serial connection. Once connected, the library allows to receive and transmit data over LoRa directly with the module. Supports micropython and desktop machines.


## Installation

1. Clone this repository `git clone https://github.com/lorenzschmid/pyRN2483.git`
2. Change into the new directory `cd rn2483`
3. Install package with `pip`: `pip install .`


## Micropython Example

    import pyb
    from lora import LoRa

    debug = True        # print debug information of current command in REPL
    serial_port = 1     # indicate UART port LoRa module is connected to
    timeout = 5000      # timeout of serial and lora reception
    tx_data = "Hello!"  # data to be send (leave empty for reception)

    # connect to module
    lora = LoRa(serial_port, timeout, timeout, debug)

    if tx_data != "":
        # transmit data
        lora.send_str(tx_data)
    else:
        # receive and print data
        rx_str = lora.recv_str()
        print(rx_str)


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
