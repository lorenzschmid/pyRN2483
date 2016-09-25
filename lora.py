DEBUG = True
DEV = None


# Create connection to LoRa module
def open_from_pyb(port=1):
    import pyb
    ser = pyb.UART(port, 57600)
    ser.init(57600,
             bits=8,
             parity=None,
             stop=1)

    global DEV
    DEV = 'pyb'

    return ser


def open_from_pc(serPort):
    import serial
    import ast
    # read config file
    # with open('deed.txt', 'r') as f:
    #     s = f.read()
    #     config = ast.literal_eval(s)
    #     print(config)
    #     serPor = config['COM']

    ser = serial.Serial('/dev/' + serPort,
                        baudrate=57600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE)
    global DEV
    DEV = 'pc'

    return ser


# Communicate with LoRa module
def write_from_pc(ser, strIn):
    # write bytes
    ser.write(b"%s\r\n" % strIn)
    return None


def write_from_pyb(ser, strIn):
    return None


def write(ser, strIn):
    if DEV == 'pc':
        return write_from_pc(ser, strIn)
    else:
        return write_from_pyb(ser, strIn)


def read_from_pc(ser):
    ret = ser.readline()
    if DEBUG:
        print '>> %s' % (ret.strip())
    return ret


def read_from_pyb(ser):
    return None


def read(ser):
    if DEV == 'pc':
        return read_from_pc(ser)
    else:
        return read_from_pyb(ser)


def send(ser, strIn, strOut=0):
    write(ser, strIn)

    # wait for answer
    ret = read(ser)

    # if requested, verify return
    if strOut is not 0:
        # verify return
        if ret.strip() != strOut:
            raise IOError()
    return True


# LoRa config functions
def set_rx_mode(ser, getsnr=0):
    try:
        # try to configure device as receiver
        send(ser, "mac pause")
        send(ser, "radio rx 0", "ok")
    except IOError:
        # abort if configuration failed
        print "RX: Configuration failed!"
    else:
        # wait for incoming data
        print "RX: Receiving..."
        ret = ser.readline()

        # strip data
        ret = ret[8:].strip()

        if DEBUG:
            print ">> %s" % ret

        if getsnr:
            write(ser, "radio get snr")
            snr = ser.readline()
            # range -128 to 127
            print ">> SNR=%s" % snr
        return ret


def set_tx_mode(ser):
    try:
        # try to configure device as receiver
        send(ser, "mac pause")
        return True
    except IOError:
        # abort if configuration failed
        print "TX: Configuration failed!"
        return False

def lora_send(tx_data):
    try:
        # try to send data
        send(ser, "radio tx "+str(tx_data), "ok")
        ret = ser.readline()
        if ret.strip() != "radio_tx_ok":
            print("expecting radio_tx_ok, received:'" + ret.strip() + "'")
            raise IOError()
    except IOError:
        print "TX: Failed to Send!"
    else:
        #read rx data here!


def init(port='pyb'):
    # open connection
    if port == 'pyb':
        ser = open_from_pyb()
    else:
        ser = open_from_pc(port)
    try:
        send(ser, "radio set mod lora", "ok")
        send(ser, "radio set freq 868000000", "ok")
        send(ser, "radio set pwr 14", "ok")
        send(ser, "radio set sf sf12", "ok")
        send(ser, "radio set afcbw 125", "ok")
        send(ser, "radio set rxbw 250", "ok")
        send(ser, "radio set fdev 5000", "ok")
        send(ser, "radio set prlen 8", "ok")
        send(ser, "radio set crc on", "ok")
        send(ser, "radio set cr 4/8", "ok")
        send(ser, "radio set wdt 0", "ok")
        send(ser, "radio set sync 12", "ok")
        send(ser, "radio set bw 250", "ok")
    except IOError:
        # abort if configuration failed
        print "Initial Configuration failed!"
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
                        default='ttyUSB0',
                        help='Serial Port ' +
                        'e.g. pyb, ttyUSB1, tty.usbserial-A5046HZ5')
    args = parser.parse_args()
    DEBUG = args.debug
    serPort = args.port
    radioModeTx = args.transmit

    init(serPort)
