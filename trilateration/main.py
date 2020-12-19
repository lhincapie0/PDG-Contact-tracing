import databaseService
import trilateration

import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import sys
import datetime
from psycopg2 import connect
from psycopg2 import OperationalError, errorcodes, errors
accessPoints = []
accessPointsMacs = []
observers = []

testDevices = ['F81F32F8AA94','60AB67B94E5D','2446C8A8C839']
testDevices2Dic = ['F81F32F8A5D4','F81F32F8A61E','F81F32F89FB4']

def handleDeviceInformation(deviceMac, accessPoints, accessPointsMacs, distanceMethod):
    dev = databaseService.fetchDeviceObserversInfo(deviceMac)
    observers = trilateration.saveObserversInfo(dev)
    momentsProfile = trilateration.handleTimeRange(observers, deviceMac)
    trilateration.trilat(momentsProfile, observers, accessPoints, accessPointsMacs,distanceMethod)

def init(distanceMethod):
  aps = databaseService.fetchAccessPointsInfo()
  accessPoints = trilateration.saveAccessPointsInfo(aps)
  apsMacs = databaseService.fetchAccessPointsMacInfo()
  for ap in apsMacs:
    for info in ap:
        accessPointsMacs.append(trilateration.handleAPMacInfo(info))
  handleDeviceInformation(testDevices2Dic[0], accessPoints, accessPointsMacs,distanceMethod)


# 3 lineal method
# 4 exponential method
init(3)
