""" Module that includes functions for GPS sensor  """

import os, sys
import serial
import time
import pynmea2
import csv
from gpio import *

ser = serial.Serial('/dev/ttyACM0', 19200, timeout = 5)
csv_data = []
collect_time = time.time() + 60

def parse_gps(serial_line):
    msg = pynmea2.parse(serial_line)
    data = (msg.longitude, msg.latitude)
    return(data)

def update_step():
    line = str(ser.readline())
    decoded_line = line[2:-5]
    if len(decoded_line) == 0: 
        print("Time out! exit. \n")
        sys.exit()
    while gps_line.find('GGA') < 0: 
        print("no GGA -- gps_line: ",gps_line)
        line = str(ser.readline())
    coord = parse_gps(decoded_line)
    if isinstance(coord, tuple): 
        print("tuple coord: ", coord)
        return(coord)
    # if isinstance(coord, tuple):
    #     print('----------------GOT COORD!!!!!----------------')
    #     print('is tuple: ' + str(coord))
    #     return(coord)
    print('not tuple: '+str(coord))

update_step()