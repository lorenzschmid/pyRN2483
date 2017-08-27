import binascii


# Module specific Exception
class LoRaException(Exception):
    '''Parent exception class for all module exceptions'''
    pass


class ConnectionError(LoRaException):
    '''Parent device (PC or pyb) failing to connect to LoRa module'''
    pass


class TransmissionError(LoRaException):
    '''Error during transmission (in LoRa or serial communication)'''
    pass


class ReceptionError(LoRaException):
    '''Error during reception (in LoRa or serial communication)'''
    pass


class TimeoutError(LoRaException):
    '''LoRa module reception timeout error'''
    pass


class ConfigurationError(LoRaException):
    '''Parent device (PC or pyb) failing to configure LoRa module for task'''
    pass


class LoRa(object):
    '''Representing a physical connection to a RN2483 LoRa module'''

    # Helper Function
    def _set_parent_dev(self):
        '''Set parent device (PC or micropython board)'''
        try:
            import pyb
        except:
            self._parent_dev = 'pc'
        else:
            self._parent_dev = 'pyb'

    # Create connection to LoRa module from parent device
    def _open(self, serPort=1):
        '''Open serial connection to LoRa module'''
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
                         timeout=self._read_timeout_serial,
                         timeout_char=self._read_timeout_serial)
            # error handling
            except:
                raise ConnectionError("No LoRa module found.")

        else:
            # via computer
            import serial

            # try to connect
            try:
                # set serial write timeout to same value as read timeout
                # to avoid being blocking for too long
                timeout = self._read_timeout_serial / 1000

                ser = serial.Serial(serPort,
                                    baudrate=57600,
                                    bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE,
                                    timeout=timeout,
                                    write_timeout=timeout)
            # error handling
            except serial.SerialException:
                raise ConnectionError("No LoRa module at given port.")
            except ValueError:
                raise ConnectionError("Wrong configuration parameter given.")

        self.port = serPort
        self._parent_ser = ser

    # End connection to parent device
    def _close(self):
        '''Close serial connection to LoRa module'''
        if self._parent_dev == 'pc':
            self._parent_ser.close()

    # Communicate with LoRa module via parent device
    def _ser_write(self, strIn):
        '''Write via serial connection to LoRa module'''
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
        '''Read via serial connection from LoRa module'''
        # read one line from parent device (blocking)
        received_bytes = self._parent_ser.readline()

        # verification of timeout
        if received_bytes is None or len(received_bytes) == 0:
            raise TimeoutError("Timeout occurred during reception.")

        # format output string
        if self._parent_dev == 'pc':
            received_bytes = received_bytes.decode('utf-8')

        # debugging
        if self._debug:
            print("LoRa:_ser_read : {}".format(received_bytes.strip()))

        return received_bytes

    def _ser_write_read_verify(self, strIn, strOut=0):
        '''Perform serial write and read and verify the read output'''
        # transmit data
        self._ser_write(strIn)

        # wait for answer
        answer = self._ser_read()

        # if requested, verify return
        if strOut is not 0:
            if answer.strip().decode() != strOut:
                # exception if LoRa module is already receiving and set to be
                # receiving again it will respond "busy" instead of "ok"
                if strIn.startswith('radio rx ') and \
                   answer.strip().decode() == 'busy':
                    pass
                else:
                    raise ReceptionError("Transmitted and received string " +
                                         "are not corresponding.")

        return answer

    # LoRa communication functions
    def recv(self):
        '''Set LoRa module in receiver mode and read received data'''
        if self._debug:
            print("LoRa:recv : Prepare for reception.")

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
                    print("LoRa:recv : SNR = {0}".format(snr))
                except ReceptionError:
                    raise ConfigurationError("Could not obtain SNR value.")

            # wait for incoming data
            if self._debug:
                print("LoRa:recv : Receiving...")
            try:
                received_data = self._ser_read()
            except (ReceptionError, TimeoutError) as e:
                raise e
            else:
                # verify if no LoRa timeout occurred
                if received_data.strip() == 'radio_err':
                    raise TimeoutError("Timeout occurred during reception.")

                # strip data
                received_data = received_data[8:].strip()

                if self._debug:
                    print("LoRa:recv : {}".format(received_data))

                return received_data

    def send(self, tx_data):
        '''Set LoRa module in transmitter mode and send data'''
        if self._debug:
            print("LoRa:send : Prepare for transmission.")

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
            if ret.strip().decode() != "radio_tx_ok":
                raise TransmissionError("No transmission confirmation " +
                                        "received.")
        except (TransmissionError, ReceptionError):
            raise TransmissionError("Error while sending.")
        else:
            if self._debug:
                print("LoRa:send : " + str(tx_data))

    def recv_str(self):
        '''Set LoRa module in receiver mode and read received ASCI string'''
        # receive data
        rx_data = self.recv()
        text = ""

        # try to convert data to string
        try:
            text = binascii.unhexlify(rx_data)
        except TypeError:
            raise ReceptionError("Received data has odd length.")
            try:
                if(len(rx_data) > 2):
                    text = binascii.unhexlify(rx_data[:-1])
            except:
                raise ReceptionError(
                    "Received data has odd length. Not recoverable.")

        return text.decode()

    def send_str(self, tx_str):
        '''Set LoRa module in transmitter mode and send ASCI string'''
        try:
            tx_data = binascii.hexlify(tx_str).decode()
        except TypeError:
            raise TransmissionError("Transmitted string cannot be converted.")
        else:
            self.send(tx_data)

    # Constructor
    def __init__(self, port, timeout_serial=2000, timeout_lora=2000,
                 debug=False):
        '''Open serial connection to LoRa module and configure it'''

        # set internal parameters
        self._read_timeout_serial = timeout_serial  # in ms
        self._read_timeout_lora = timeout_lora      # in ms, 0 = endless
        self._debug = debug

        try:
            if self._debug:
                print("LoRa:__init__ : Start initialization.")

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

            # set reception timeout
            if self._read_timeout_lora > 0:
                self._ser_write_read_verify("radio set wdt {}".format(
                    self._read_timeout_lora), "ok")

        except (TransmissionError, ReceptionError):
            raise ConfigurationError("Initial configuration failed.")
        else:
            if self._debug:
                print("LoRa:__init__ : Connection established and " +
                      "configuration completed successfully.")

    # Destructor
    def __exit__(self, exc_type, exc_value, traceback):
        '''Close serial connection to LoRa module'''
        self._close()

    def __enter__(self):
        return self

    def __repr__(self):
        return "<LoRa module connection on port %d>".format(self.port)
