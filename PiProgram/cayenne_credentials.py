#!/usr/bin/env python3
"""
Cayenne Login Credentials
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"
__license__ = "MIT"

import enum


MQTT_PORT = 8883
MQTT_LOOP_TIME_SECONDS = 5

class VIRTUAL_CHANNEL(enum.Enum):
    STATION_1_CUMULATIVE_OZ = 1
    STATION_2_CUMULATIVE_OZ = 2
    STATION_3_CUMULATIVE_OZ = 3
    STATION_4_CUMULATIVE_OZ = 4
    TEMPERATURE             = 5