import lora

class JoinError(lora.LoRaException):
    '''Parent device (PC or pyb) failing to join LoRaWAN'''
    pass

class LoraWAN(lora.LoRa):

    def config_otaa(self, appkey=None, appeui=None, deveui=None):
        ''' Configure Over The Air Authentication '''
        self._ser_write_read_verify("mac set adr on", "ok")

        self._ser_write("sys get hweui")
        hweui = self._ser_read()
        self._ser_write_read_verify("mac set deveui {0}".format(deveui), "ok")
        self._ser_write_read_verify("mac set appkey {0}".format(appkey), "ok")
        self._ser_write_read_verify("mac set appeui {0}".format(appeui), "ok")
        self._ser_write_read_verify("mac save", "ok")
        self.wan_mode = "otaa"
        return(hweui)

    def config_abp(self, nwskey=None, appskey=None, devaddr=None):
        ''' Configure for ABP join '''
        self._ser_write_read_verify("mac set adr on", "ok")

        self._ser_write_read_verify("mac set nwkskey {0}".format(nwskey), "ok")
        self._ser_write_read_verify("mac set appskey {0}".format(appskey), "ok")
        self._ser_write_read_verify("mac set devaddr {0}".format(devaddr), "ok")
        self._ser_write_read_verify("mac save", "ok")
        self.wan_mode = "abp"

    def join(self):
        self._ser_write_read_verify("mac resume", "ok")
        self._ser_write_read_verify("mac join {}".format(self.wan_mode), "ok")
        res = self._parent_ser.readline()
        while not res:
            res = self._parent_ser.readline()
        res = res.strip().decode()
        if res != 'accepted':
            raise JoinError("unable to join LoRaWAN: {}".format(res))
        if self._debug:
            print("Joined LoRa WAN")

    def send_uplink(self, data, type="uncnf", portno=4):
        '''Send LoRaWan uplink'''
        if self._debug: print("LoRaWan:send : Sending...")

        self._ser_write_read_verify("mac resume")
        try:
            cmd = "mac tx {} {} {}".format(type, portno, data)
            self._ser_write_read_verify(cmd, "ok")

            # read out transmission verification
            ret = self._parent_ser.readline()
            while not ret:
                ret = self._parent_ser.readline()
            if ret.strip().decode() != "mac_tx_ok":
                raise lora.TransmissionError(ret.strip().decode())
        finally:
            self._ser_write_read_verify("mac pause")
