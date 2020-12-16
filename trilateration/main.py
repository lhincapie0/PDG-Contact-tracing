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

def groupedByDate(item):
    d = parse(item.get(seentime))
    return d

def handleDeviceInformation(deviceMac, accessPoints, accessPointsMacs):
    dev = databaseService.fetchDeviceObserversInfo(deviceMac)
    observers = trilateration.saveObserversInfo(dev)
    momentsProfile = trilateration.handleTimeRange(observers, deviceMac)
    trilateration.trilat(momentsProfile, observers, accessPoints, accessPointsMacs)

def init():
  aps = databaseService.fetchAccessPointsInfo()
  accessPoints = trilateration.saveAccessPointsInfo(aps)
  apsMacs = databaseService.fetchAccessPointsMacInfo()
  for ap in apsMacs:
    for info in ap:
        accessPointsMacs.append(trilateration.handleAPMacInfo(info))
  handleDeviceInformation('F81F32F8A61E', accessPoints, accessPointsMacs)



init()
