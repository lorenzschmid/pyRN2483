
class LoRa(object):

    DEBUG = True
    parent_ser = None
    parent_dev = None

    # Helper Function
    def running_on_pyb(self):
        try:
            import pyb
        except:
            self.parent_dev = 'pc'
        else:
            self.parent_dev = 'pyb'

    # Create connection to LoRa module from parent device
    def open(self, serPort=1):
        if self.parent_dev == 'pyb':
            # via micropython board
            import pyb

            # try to connect
            try:
                ser = pyb.UART(serPort, 57600)
                ser.init(57600,
                         bits=8,
                         parity=None,
                         stop=1)
            # error handling
            except:
                return IOError("Failed to create serial connection to LoRa " +
                               "module.")

        else:
            # via computer
            import serial

            # try to connect
            try:
                ser = serial.Serial('/dev/' + serPort,
                                    baudrate=57600,
                                    bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE)
            # error handling
            except SerialException:
                return IOError("Failed to create serial connection to LoRa " +
                               "module: no device at given port.")
            except ValueError:
                return IOError("Failed to create serial connection to LoRa " +
                               "module: Wrong configuration parameter given.")

        self.parent_ser = ser

    # End connection to parent device
    def close(self):
        if self.parent_dev == 'pc':
            self.parent_ser.close()

    # Communicate with LoRa module via parent device
    def ser_write(self, strIn):
        # format input string
        if self.parent_dev == 'pc':
            data = "%s\r\n" % strIn
            data = data.encode('utf-8')
        else:
            data = "%s\r\n" % strIn

        # write data to parent device
        self.parent_ser.write(data)

    def ser_read(self):
        # read one line from parent device
        ret = self.parent_ser.readline()
        if DEBUG:
            print(">> %s" % (ret.strip()))

        # format output string
        if self.parent_dev == 'pc':
            ret = ret.decode('utf-8')

        return ret

    def ser_write_read_verify(self, strIn, strOut=0):
        # send data
        self.ser_write(strIn)

        # wait for answer
        ret = self.ser_read()

        # if requested, verify return
        if strOut is not 0:
            # verify return
            if ret.strip() != strOut:
                raise IOError("Unexpected return value upon serial " +
                              "transmission with parent device.")

    # LoRa communication functions
    def recv(self, get_snr=False):
        try:
            # try to configure device as receiver
            self.ser_write_read_verify("mac pause")
            self.ser_write_read_verify("radio rx 0", "ok")
        except IOError:
            raise IOError("LoRa modul could not be configured as receiver.")
        else:
            # obtain SNR value
            if get_snr:
                try:
                    self.ser_write("radio get snr")
                    snr = self.ser_read()
                    # range -128 to 127
                    print(">> SNR=%s" % snr)
                except IOError:
                    raise IOError("Could not obtain SNR value of LoRa module.")

            # wait for incoming data
            print("RX: Receiving...")
            try:
                ret = self.ser_read()
            except IOError:
                raise IOError("Error while in receiver mode.")
            else:
                # strip data
                ret = ret[8:].strip()

                if DEBUG:
                    print(">> %s" % ret)
                return ret

    def send(self, tx_data):
        # try to configure device as receiver
        try:
            self.ser_write_read_verify("mac pause")
        except IOError:
            raise IOError("LoRa module could not be configured as " +
                          "transmitter.")

        try:
            # send data
            self.ser_write_read_verify("radio tx " + str(tx_data), "ok")

            # read out send verification
            ret = self.ser_read()
            if ret.strip() != "radio_tx_ok":
                raise IOError("Missing sent confirmation upon transmission.")
        except IOError:
            print("Error while sending data.")
        else:
            if DEBUG:
                print("Sent Data: " + str(tx_data))

    # Constructor
    def __init__(self, port):
        try:
            # get parent device
            self.running_on_pyb()

            # open serial connection on parent device
            self.open(port)

            # configure LoRa module via parent device
            self.ser_write_read_verify("radio set mod lora", "ok")
            self.ser_write_read_verify("radio set freq 868000000", "ok")
            self.ser_write_read_verify("radio set pwr 14", "ok")
            self.ser_write_read_verify("radio set sf sf12", "ok")
            self.ser_write_read_verify("radio set afcbw 125", "ok")
            self.ser_write_read_verify("radio set rxbw 250", "ok")
            self.ser_write_read_verify("radio set fdev 5000", "ok")
            self.ser_write_read_verify("radio set prlen 8", "ok")
            self.ser_write_read_verify("radio set crc on", "ok")
            self.ser_write_read_verify("radio set cr 4/8", "ok")
            self.ser_write_read_verify("radio set wdt 0", "ok")
            self.ser_write_read_verify("radio set sync 12", "ok")
            self.ser_write_read_verify("radio set bw 250", "ok")

        except IOError:
            raise IOError("Initial LoRa Configuration failed.")
        else:
            if DEBUG:
                print ("Connection established and configuration of LoRa " +
                       "module completed succesfuly.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


# execute only if run as a script
if __name__ == "__main__":
    import argparse

    # command line arguments and parsing
    parser = argparse.ArgumentParser(description='LoRa Script Arguments')
    parser.add_argument('-d', '--debug',
                        action='store_true', help='debug mode')
    parser.add_argument('-tx', '--transmit',
                        default='',
                        action='store_true', help='Data to transmit')
    parser.add_argument('-p', '--port',
                        default='ttyUSB0',
                        help='Serial Port ' +
                        'e.g. pyb, ttyUSB1, tty.usbserial-A5046HZ5')
    args = parser.parse_args()
    DEBUG = args.debug
    serPort = args.port
    tx_data = args.transmit

    lora = LoRa(serPort)
    if tx_data != "":
        lora.send(tx_data)
    else:
        lora.recv()
