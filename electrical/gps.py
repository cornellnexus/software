""" Module that includes functions for GPS sensor  """

import serial
import time
import pynmea2
import csv
from gpio import *
from ublox_gps import UbloxGps


class GPS:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyACM0', 19200, timeout=5)
        self.gps = UbloxGps(self.ser)

    """ get_gps: returns the coordinate (long, lat)"""

    def get_gps(self):
        """
        gps_line = str(gps.stream_nmea())
        while gps_line.find("GGA") < 0:
            gps_line = str(gps.stream_nmea())
        coord = self.parse_gps(gps_line)
        if coord is not None:
            return (coord)
        """
        geo = self.gps.geo_coords()
        return {"long": geo.lon, "lat": geo.lat}

    """ parse_gps[gps_line]: helper that takes in serial gps data and returns
        a coord in the form (longitude, latitude).
        precondition: gps_line must be a string of pynmea format.
    """

    def parse_gps(self, gps_line):
        msg = pynmea2.parse(gps_line)
        data = {"long": msg.longitude, "lat": msg.latitude}
        return (data)