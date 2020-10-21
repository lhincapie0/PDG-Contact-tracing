from rssi import RSSI_Localizer
import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import numpy as np
import sys
import datetime
from psycopg2 import connect
from psycopg2 import OperationalError, errorcodes, errors
from itertools import groupby
from operator import itemgetter
import json


accesspoints = []
observers = []
class access_point_profile:
    def __init__(self, host_name, mac, policy, location):
        self.host_name = host_name
        self.mac = mac
        self.policy = policy
        self.location = location
        ## Should investigate these values
        self.signal_attenuation = 3
        self.reference_signal = -40
        self.reference_distance = 4
        self.x = 0
        self.y = 0

class observers_profile:
    def __init__(self, mac, ap_mac, rssi, seentime):
        self.mac = mac
        self.ap_mac = ap_mac
        self.rssi = rssi
        self.seentime = seentime

def generateRandomLocation(ap):
    ed_e = ap.location.find("Edificio E")
    ed_d = ap.location.find("Edificio D")

    if (ed_e > 0):
        ap.x = np.random.randint(100, 200)
        ap.y = np.random.randint(0, 100)
    if (ed_d > 0):
        ap.x = np.random.randint(300, 400)
        ap.y = np.random.randint(100, 150)
    return ap

connection = None
try:
    connection = psycopg2.connect(
        user="postgres", password="postgres", host="127.0.0.1", port="5432", database="PDGAccesPointDB")
    cursor = connection.cursor()
    postgreSQL_select_Query = "SELECT * FROM spaces;"
    cursor.execute(postgreSQL_select_Query)
    allData = cursor.fetchall()
    seq = allData
    #seq.sort(key = lambda x: x[0])
    groups = groupby(seq, lambda x: x[0])
    aps = [[item[:] for item in data] for (key, data) in groups]
    for element in aps:
        for ap in element:
            access_point = access_point_profile(ap[1], ap[2], ap[6], ap[14])
            accesspoints.append(generateRandomLocation(access_point))

    postgreSQL_select_Query = """SELECT res.mac, res.seenTime, spaces."MAC", res.rssi, res.x, res.y 
        FROM(SELECT 
        json_array_elements(data->'data'->'observations')->>'clientMac' as mac,
        json_array_elements(data->'data'->'observations')->>'seenEpoch' as seenEpoch,
        json_array_elements(data->'data'->'observations')->>'seenTime' as seenTime,
        json_array_elements( json_array_elements(data->'data'->'observations')->'deviceObservers') ->> 'apMac' as apMac,
        json_array_elements( json_array_elements(data->'data'->'observations')->'deviceObservers') ->> 'rssi' as rssi,
        json_array_elements(data->'data'->'observations') ->> 'x' as x,
        json_array_elements(data->'data'->'observations') ->> 'y' as y
        FROM example
        ORDER BY mac,seenTime) as res, spaces
        WHERE res.mac='322A1BD104C2' 
        and res.apMac = spaces."MAC";"""
    cursor.execute(postgreSQL_select_Query)
    allData = cursor.fetchall()
    seq = allData
    #seq.sort(key = lambda x: x[0])
    groups = groupby(seq, lambda x: x[0])
    obs = [[item[:] for item in data] for (key, data) in groups]
    for element in obs:
        for ob in element:
            observer = observers_profile(ob[0], ob[2], ob[3], ob[1])
            # accesspoints.append(generateRandomLocation(access_point))

finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
