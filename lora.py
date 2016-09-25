DEBUG = True
DEV = None


# Create connection to LoRa module
def open_from_pyb(serPort=1):
    import pyb
    ser = pyb.UART(serPort, 57600)
    ser.init(57600,
             bits=8,
             parity=None,
             stop=1)

    global DEV
    DEV = 'pyb'

    return ser


def open_from_pc(serPort):
    import serial
    ser = serial.Serial('/dev/' + serPort,
                        baudrate=57600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE)
    global DEV
    DEV = 'pc'

    return ser


# Communicate with LoRa module
def write_to_lora(ser, strIn):
    # write bytes from PC
    if DEV == 'pc':
        data = b"%s\r\n" % strIn
    else:
        data = "%s\r\n" % strIn
    ser.write_to_lora(data)


def read_from_lora(ser):
    ret = ser.readline()
    if DEBUG:
        print '>> %s' % (ret.strip())
    return ret


def communicate_with_lora(ser, strIn, strOut=0):
    write_to_lora(ser, strIn)

    # wait for answer
    ret = read_from_lora(ser)

    # if requested, verify return
    if strOut is not 0:
        # verify return
        if ret.strip() != strOut:
            raise IOError('Unexpected return value!')
    return True


# LoRa config functions
def set_rx_mode(ser, get_snr=0):
    try:
        # try to configure device as receiver
        communicate_with_lora(ser, "mac pause")
        communicate_with_lora(ser, "radio rx 0", "ok")
    except IOError:
        print "RX: Configuration failed!"
    else:
        # obtain SNR value
        if get_snr:
            write_to_lora(ser, "radio get snr")
            snr = read_from_lora(ser)
            # range -128 to 127
            print ">> SNR=%s" % snr

        # wait for incoming data
        print "RX: Receiving..."
        ret = read_from_lora(ser)

        # strip data
        ret = ret[8:].strip()

        if DEBUG:
            print ">> %s" % ret
        return ret


def set_tx_mode(ser):
    try:
        # try to configure device as receiver
        communicate_with_lora(ser, "mac pause")
    except IOError:
        print "TX: Configuration failed!"
    else:
        try:
            # try to send data
            communicate_with_lora(ser, "radio tx FF", "ok")
            ret = read_from_lora()
            if ret.strip() != "radio_tx_ok":
                raise IOError()
        except IOError:
            print "TX: Failed to Send!"


def init(port='pyb'):
    # open connection
    if port == 'pyb':
        ser = open_from_pyb()
    else:
        ser = open_from_pc(port)
    try:
        communicate_with_lora(ser, "radio set mod lora", "ok")
        communicate_with_lora(ser, "radio set freq 868000000", "ok")
        communicate_with_lora(ser, "radio set pwr 14", "ok")
        communicate_with_lora(ser, "radio set sf sf12", "ok")
        communicate_with_lora(ser, "radio set afcbw 125", "ok")
        communicate_with_lora(ser, "radio set rxbw 250", "ok")
        communicate_with_lora(ser, "radio set fdev 5000", "ok")
        communicate_with_lora(ser, "radio set prlen 8", "ok")
        communicate_with_lora(ser, "radio set crc on", "ok")
        communicate_with_lora(ser, "radio set cr 4/8", "ok")
        communicate_with_lora(ser, "radio set wdt 0", "ok")
        communicate_with_lora(ser, "radio set sync 12", "ok")
        communicate_with_lora(ser, "radio set bw 250", "ok")
    except IOError:
        print "Initial LoRa Configuration failed!"
    else:
        if radioModeTx:
            set_tx_mode(ser)
        else:
            rxCount = 0
            while(1):
                set_rx_mode(ser, 1)
                rxCount = rxCount + 1
                print "rx packet %d" % rxCount
    print "end"
    ser.close()


# execute only if run as a script
if __name__ == "__main__":
    import argparse

    # command line arguments and parsing
    parser = argparse.ArgumentParser(description='LoRa Script Arguments')
    parser.add_argument('-d', '--debug',
                        action='store_true', help='debug mode')
    parser.add_argument('-tx', '--transmit',
                        action='store_true', help='Set Radio TX Mode')
    parser.add_argument('-p', '--port',
                        default='pyb',
                        help='Serial Port ' +
                        'e.g. pyb, ttyUSB1, tty.usbserial-A5046HZ5')
    args = parser.parse_args()
    DEBUG = args.debug
    serPort = args.port
    radioModeTx = args.transmit

    init(serPort)
