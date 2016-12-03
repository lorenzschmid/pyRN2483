import pyb
from lora import LoRa

debug = True
ser_port = 1
tx_data = ""

lora = LoRa(ser_port, debug)
if tx_data != "":
    lora.send(tx_data)
else:
    lora.recv()
