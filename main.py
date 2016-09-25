# main.py -- put your code here!
import pyb
from lora import LoRa

DEBUG = True
ser_port = 1
tx_data = ""

lora = LoRa(ser_port)
if tx_data != "":
    lora.send(tx_data)
else:
    lora.recv()
