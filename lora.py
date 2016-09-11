import serial

DEBUG = True


def send(ser, strIn, strOut=0):
    # write bytes
    ser.write(b"%s\r\n" % strIn)

    # wait for answer
    ret = ser.readline()
    if DEBUG:
        print ">> send ret: %s" % ret.strip()

    # if requested, verify return
    if strOut is not 0:
        # verify return
        if ret.strip() != strOut:
            raise IOError()
    return True


def set_rx_mode(ser):
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


with serial.Serial('/dev/ttyUSB0',
                   baudrate=57600,
                   bytesize=serial.EIGHTBITS,
                   parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE) as ser:
    #print ser.is_open
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
        set_tx_mode(ser)
    print "end"
    ser.close()
