#!/usr/bin/env python3
import binascii

# Module specific Exception
class ConnectionError(Exception):
    pass


class TransmissionError(Exception):
    pass


class ReceptionError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class LoRa(object):

    # Helper Function
    def _set_parent_dev(self):
        try:
            import pyb
        except:
            self._parent_dev = 'pc'
        else:
            self._parent_dev = 'pyb'

    # Create connection to LoRa module from parent device
    def _open(self, serPort=1):
        if self._parent_dev == 'pyb':
            # via micropython board
            import pyb

            # try to connect
            try:
                ser = pyb.UART(serPort, 57600)
                ser.init(baudrate=57600,
                         bits=8,
                         parity=None,
                         stop=1,
                         timeout=self._read_timeout,
                         timeout_char=self._read_timeout)
            # error handling
            except:
                raise ConnectionError("No LoRa module found.")

        else:
            # via computer
            import serial

            # try to connect
            try:
                ser = serial.Serial('/dev/' + serPort,
                                    baudrate=57600,
                                    bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE,
                                    timeout=self._read_timeout)
            # error handling
            except serial.SerialException:
                raise ConnectionError("No LoRa module at given port.")
            except ValueError:
                raise ConnectionError("Wrong configuration parameter given.")

        self.port = serPort
        self._parent_ser = ser

    # End connection to parent device
    def _close(self):
        if self._parent_dev == 'pc':
            self._parent_ser.close()

    # Communicate with LoRa module via parent device
    def _ser_write(self, strIn):
        # reset error handling flags
        transmit_failed = False
        transmit_incomplete = False

        if self._parent_dev == 'pc':
            # format input string
            data = "{}\r\n".format(strIn)
            data = data.encode('utf-8')

            # try to send data (blocking)
            try:
                transmitted_bytes = self._parent_ser.write(data)
            except serial.SerialTimeoutException:
                transmit_failed = True
            else:
                if transmitted_bytes < len(data):
                    transmit_incomplete = True
        else:
            # format input string
            data = "{}\r\n".format(strIn)

            # send data (blocking)
            transmitted_bytes = self._parent_ser.write(data)

            # verify transmit
            if transmitted_bytes == 0:
                transmit_failed = True
            elif transmitted_bytes < len(data):
                transmit_incomplete = True

        # error handling
        if transmit_failed:
            raise TransmissionError("Write failed due to timeout.")
        if transmit_incomplete:
            raise TransmissionError("Write was incomplete.")

        # debugging
        if self._debug:
            print("LoRa:_ser_write : {}".format(data))

    def _ser_read(self):
        # read one line from parent device (blocking)
        received_bytes = self._parent_ser.readline()

        # verification
        if received_bytes is None or len(received_bytes) == 0:
            raise ReceptionError("Timeout occurred during reception.")

        # format output string
        if self._parent_dev == 'pc':
            received_bytes = received_bytes.decode('utf-8')

        # second verification
        if received_bytes.strip() == 'busy':
            raise ReceptionError("Transmitter is busy.")

        # debugging
        if self._debug:
            print("LoRa:_ser_read : {}".format(received_bytes.strip()))

        return received_bytes

    def _ser_write_read_verify(self, strIn, strOut=0):
        # transmit data
        self._ser_write(strIn)

        # wait for answer
        answer = self._ser_read()

        # if requested, verify return
        if strOut is not 0:
            if answer.strip() != strOut:
                raise ReceptionError("Transmitted and received string are " +
                                     "not corresponding.")

        return answer

    # LoRa communication functions
    def recv(self):
        # try to configure device as receiver
        try:
            self._ser_write_read_verify("mac pause")
            self._ser_write_read_verify("radio rx 0", "ok")
        except (TransmissionError, ReceptionError):
            raise ConfigurationError("Configuration as receiver failed.")
        else:
            # obtain SNR value
            if self._debug:
                try:
                    self._ser_write("radio get snr")
                    snr = self._ser_read()
                    # range -128 to 127
                    print("LoRa:recv : SNR = %d".format(snr))
                except ReceptionError:
                    raise ConfigurationError("Could not obtain SNR value.")

            # wait for incoming data
            if self._debug:
                print("LoRa:recv : Receiving...")
            try:
                received_data = self._ser_read()
            except ReceptionError as e:
                raise e
            else:
                # strip data
                received_data = received_data[8:].strip()

                if self._debug:
                    print("LoRa:recv : {}".format(received_data))

                return received_data

    def send(self, tx_data):
        # try to configure device as transmitter
        try:
            self._ser_write_read_verify("mac pause")
        except (TransmissionError, ReceptionError):
            raise ConfigurationError("Configuration as transmitter failed.")

        if self._debug:
            print("LoRa:send : Sending...")
        try:
            # send data
            self._ser_write_read_verify("radio tx " + str(tx_data), "ok")

            # read out transmission verification
            ret = self._ser_read()
            if ret.strip() != "radio_tx_ok":
                raise TransmissionError("No transmission confirmation " +
                                        "received.")
        except (TransmissionError, ReceptionError):
            raise TransmissionError("Error while sending.")
        else:
            if self._debug:
                print("LoRa:send : " + str(tx_data))

    def send_str(self, tx_str):
        self.send(binascii.hexlify(tx_str))

    def recv_str(self):
        rx_data = self.recv()
        text = ""
        try:
            text = binascii.unhexlify(rx_data)
        except (TypeError) as e:
            raise ReceptionError("Received data has odd length")
            if(len(rx_data) > 2):
                text = binascii.unhexlify(rx_data[:-1])
        return text


    # Constructor
    def __init__(self, port, timeout=1000, debug=False):
        self._read_timeout = timeout
        self._debug = debug

        try:
            # get parent device
            self._set_parent_dev()

            # open serial connection on parent device
            self._open(port)

            # configure LoRa module via parent device
            self._ser_write_read_verify("radio set mod lora", "ok")
            self._ser_write_read_verify("radio set freq 868000000", "ok")
            self._ser_write_read_verify("radio set pwr 14", "ok")
            self._ser_write_read_verify("radio set sf sf12", "ok")
            self._ser_write_read_verify("radio set afcbw 125", "ok")
            self._ser_write_read_verify("radio set rxbw 250", "ok")
            self._ser_write_read_verify("radio set fdev 5000", "ok")
            self._ser_write_read_verify("radio set prlen 8", "ok")
            self._ser_write_read_verify("radio set crc on", "ok")
            self._ser_write_read_verify("radio set cr 4/8", "ok")
            self._ser_write_read_verify("radio set wdt 0", "ok")
            self._ser_write_read_verify("radio set sync 12", "ok")
            self._ser_write_read_verify("radio set bw 250", "ok")

        except (TransmissionError, ReceptionError) as e:
            raise ConfigurationError("Initial configuration failed: " + str(e))
        else:
            if self._debug:
                print("LoRa:__init__ : Connection established and " +
                      "configuration completed successfully.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._close()

    def __repr__(self):
        return "<LoRa module connection on port %d>".format(self.port)


# execute only if run as a script
if __name__ == "__main__":
    import argparse

    # command line arguments and parsing
    parser = argparse.ArgumentParser(description='LoRa Script Arguments')
    parser.add_argument('-d', '--debug',
                        action='store_true', help='debug mode')
    parser.add_argument('-t', '--transmit',
                        default='',
                        help='Data to transmit')
    parser.add_argument('-r', '--receive',
                        default='10',
                        help='Timeout upon reception')
    parser.add_argument('-p', '--port',
                        default='ttyUSB0',
                        help='Serial Port ' +
                        'e.g. pyb, ttyUSB1, tty.usbserial-A5046HZ5')
    args = parser.parse_args()

    debug = args.debug
    serial_port = args.port
    tx_data = args.transmit
    timeout = int(args.receive)

    # create connection
    try:
        lora = LoRa(serial_port, timeout, debug)
    except ConfigurationError as e:
        print("Error occurred: " + str(e))

    # start operation
    if tx_data != "":
        try:
            lora.send_str(tx_data)
        except (ConfigurationError, TransmissionError) as e:
            print("Error occurred: " + str(e))
    else:
        while True:
            try:
                lora.recv_str()
            except (ConfigurationError, ReceptionError) as e:
                print("Error occurred: " + str(e))
                break
