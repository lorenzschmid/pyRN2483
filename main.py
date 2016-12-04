import pyb
from lora import LoRa

debug = True
serial_port = 1
timeout = 1000
tx_data = ""

lora = LoRa(serial_port, timeout, timeout, debug)
if tx_data != "":
    lora.send(tx_data)
else:
    lora.recv()
