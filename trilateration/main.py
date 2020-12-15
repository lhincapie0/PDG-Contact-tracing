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
observers = []

def groupedByDate(item):
    d = parse(item.get(seentime))
    return d



def init():
  aps = databaseService.fetchAccessPointsInfo()
  accessPoints = trilateration.saveAccessPointsInfo(aps)
  dev = databaseService.fetchDeviceObserversInfo('F81F32F89FB4')
  observers = trilateration.saveObserversInfo(dev)
  trilateration.handleTimeRange(observers)

init()
