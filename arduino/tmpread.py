import serial
import time
from datetime import datetime

baud = 57600

with serial.Serial('/dev/cu.usbserial-1420', baud, timeout=3, write_timeout=5) as my_serial:
    while(True):
        line = my_serial.readline()
        print(line.decode().replace("\n", "").split(" "))
        print(datetime.now())
