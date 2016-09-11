import serial
import argparse


# Functions
def send_no_ack(ser, strIn):
    # write bytes
    ser.write(b"%s\r\n" % strIn)


def send(ser, strIn, strOut=0):
    send_no_ack(ser, strIn)

    # wait for answer
    ret = ser.readline()
    if DEBUG:
        print ">> %s" % ret.strip()

    # if requested, verify return
    if strOut is not 0:
        # verify return
        if ret.strip() != strOut:
            raise IOError()
    return True


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
            send_no_ack(ser, "radio get snr")
            snr = ser.readline()
            # range -128 to 127
            print ">> SNR=%s" % snr
        return ret


def set_tx_mode(ser):
    try:
        # try to configure device as receiver
        send(ser, "mac pause")
    except IOError:
        # abort if configuration failed
        print "TX: Configuration failed!"
    else:
        try:
            # try to send data
            send(ser, "radio tx FF", "ok")
            ret = ser.readline()
            if ret.strip() != "radio_tx_ok":
                print("expecting radio_tx_ok, received:'" + ret.strip() + "'")
                raise IOError()
        except IOError:
            print "TX: Failed to Send!"


# execute only if run as a script
if __name__ == "__main__":

    # command line arguments and parsing
    parser = argparse.ArgumentParser(description='LoRa Script Arguments')
    parser.add_argument('-d', '--debug',
                        action='store_true', help='debug mode')
    parser.add_argument('-tx', '--transmit',
                        action='store_true', help='Set Radio TX Mode')
    parser.add_argument('-p', '--port',
                        default='ttyUSB0',
                        help='Serial Port ' +
                        'e.g. ttyUSB1, tty.usbserial-A5046HZ5')
    args = parser.parse_args()
    DEBUG = args.debug
    serPort = args.port
    radioModeTx = args.transmit

    # open connection
    with serial.Serial('/dev/' + serPort,
                       baudrate=57600,
                       bytesize=serial.EIGHTBITS,
                       parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE) as ser:
        # print ser.is_open
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
