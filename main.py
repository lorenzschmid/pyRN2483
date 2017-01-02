import pyb
from lora import LoRa

debug = True
serial_port = 1
timeout = 5000
tx_data = "Hello!"

lora = LoRa(serial_port, timeout, timeout, debug)
if tx_data != "":
    lora.send_str(tx_data)
else:
    rx_str = lora.recv_str()
    print(rx_str)
