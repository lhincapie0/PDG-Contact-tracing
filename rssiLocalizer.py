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
import csv
import os
import openpyxl


accesspoints = []
observers = []
default_distance_AP = 1
default_signal_AP = -80
lastObserver = []

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
    def __init__(self, mac, ap_mac, rssi, seentime, time):
        self.mac = mac
        self.ap_mac = ap_mac
        self.rssi = rssi
        self.seentime = seentime
        self.time = time


class seen_profile:
    def __init__(self, seentimeId):
        self.seentimeId = seentimeId
        self.observers = []

def generateRandomLocation(ap):
    ed_e = ap.location.find("Edificio E")
    ed_d = ap.location.find("Edificio D")
    ed_sae = ap.location.find("Casa_SAE")
    ed_bien = ap.location.find("Bienestar")

    if (ed_e > 0):
        x = np.random.rand() *100 +200
        y = np.random.rand() *100 +200
        ap.x = x
        ap.y = y
    if (ed_d > 0):
        x = np.random.rand() *100 + 300
        y = np.random.rand()  *100 + 300
        ap.x = x
        ap.y = y
    if (ed_sae > 0):
        x = np.random.rand()  *100 + 700
        y = np.random.rand() *100 + 700
        ap.x = x
        ap.y = y
    if (ed_bien > 0):
        x = np.random.rand()  *100 + 400
        y = np.random.rand() *100 + 400
        ap.x = x
        ap.y = y


    return ap

def evaluateMatches(list, devName):
    print("evaluating observers for... "+devName)
    i = 0
    fileName = devName+'.csv'
    if os.path.exists(fileName):
        os.remove(fileName)

    for observer in list:
        for accesspoint in accesspoints:
            with open (fileName, 'a') as csvfile:
                fieldnames = ['Device Mac', 'AP Mac', 'Seentime', 'Distance from AP']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if(accesspoint.mac == observer.ap_mac):
                    calculateDistance(observer, accesspoint, devName, writer)

def calculateDistance(observer, accesspoint, devName, writer):
    accessPoint = {
    'signalAttenuation': 3,
    'location': {
        'y': accesspoint.y,
        'x': accesspoint.x
    },
    'reference': {
        'distance': default_distance_AP,
        'signal': -default_signal_AP,
    },
        'name': accesspoint.host_name
    }
    rssi_localizer_instance = RSSI_Localizer(accessPoints=accessPoint)
    signalStrength = observer.rssi
    distance = rssi_localizer_instance.getDistanceFromAP(
        accessPoint, int(observer.rssi))
    writer.writerow({'Device Mac':devName, 'AP Mac': accesspoint.host_name, 'Seentime': observer.seentime, 'Distance from AP': distance['distance']})
    lastObserver = observer


connection = None
try:
    connection = psycopg2.connect(
        user="postgres", password="postgres", host="127.0.0.1", port="5432", database="PDGAccesPointDB")
    cursor = connection.cursor()
    postgreSQL_select_Query = "SELECT * FROM spaces;"
    cursor.execute(postgreSQL_select_Query)
    allData = cursor.fetchall()
    seq = allData

    groups = groupby(seq, lambda x: x[0])
    aps = [[item[:] for item in data] for (key, data) in groups]
    for element in aps:
        for ap in element:
            access_point = access_point_profile(ap[1], ap[2], ap[6], ap[14])
            access_point = generateRandomLocation(access_point)
            accesspoints.append(access_point)

    macs_list = ['60AB67B94E5D', '8035C14D35F4', '58E6BA7C10E8',
                     '8875989F746A', '34F64B76676D', '2446C8A8C839']
    for mac_device in macs_list:
        print(mac_device)
        seentimes = []
        ## CELULAR DAVID
        postgreSQL_select_Query = """
             SELECT res.mac, res.seenTime, spaces."MAC", res.rssi, res.seenEpoch
            FROM(SELECT
            json_array_elements(data->'data'->'observations')->>'clientMac' as mac,
            json_array_elements(data->'data'->'observations')->>'seenEpoch' as seenEpoch,
            json_array_elements(data->'data'->'observations')->>'seenTime' as seenTime,
            json_array_elements( json_array_elements(data->'data'->'observations')->'deviceObservers') ->> 'apMac' as apMac,
            json_array_elements( json_array_elements(data->'data'->'observations')->'deviceObservers') ->> 'rssi' as rssi
            FROM exampleoctober e
            ORDER BY mac,seenTime) as res, spaces
            WHERE res.apMac = spaces."MAC"
            and res.mac='"""+mac_device+"';"""
        cursor.execute(postgreSQL_select_Query)
        allData = cursor.fetchall()
        seq = allData
        groups = groupby(seq, lambda x: x[0])
        obs = [[item[:] for item in data] for (key, data) in groups]
        for element in obs:
            for ob in element:
                observer = observers_profile(ob[0], ob[2], ob[3], ob[1], ob[4])
                observers.append(observer)
                seen = seen_profile(ob[1])
        evaluateMatches(observers, mac_device)

        #for seen in seentimes:
            ##print(seen.seentimeId)
            #print(len(seen.observers))


finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")

        #evaluate()

