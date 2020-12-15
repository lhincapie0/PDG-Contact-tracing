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


POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = "5432"
DATABASE_NAME = "PDGAccesPointDB"

def fetchDeviceObserversInfo(mac_device):
    print("Starting to fetch device observers information for device "+ mac_device)
    connection = None
    try:
        connection = psycopg2.connect(
            user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT, database=DATABASE_NAME)
        cursor = connection.cursor()
        postgreSQL_select_Query = """
            SELECT res.mac, res.seenTime, res.rssi, res.seenEpoch, spaces."Host Name"
            FROM(SELECT
            json_array_elements(data->'data'->'observations')->>'clientMac' as mac,
            json_array_elements(data->'data'->'observations')->>'seenEpoch' as seenEpoch,
            json_array_elements(data->'data'->'observations')->>'seenTime' as seenTime,
            json_array_elements( json_array_elements(data->'data'->'observations')->'deviceObservers') ->> 'apMac' as apMac,
            json_array_elements( json_array_elements(data->'data'->'observations')->'deviceObservers') ->> 'rssi' as rssi
            FROM pruebasdiciembre e
            ORDER BY mac,seenTime) as res, spaces
            WHERE res.apMac = spaces."MAC"
            and res.mac='"""+mac_device+"';"""
        cursor.execute(postgreSQL_select_Query)
        allData = cursor.fetchall()
        seq = allData

        groups = groupby(seq, lambda x: x[0])
        observers = [[item[:] for item in data] for (key, data) in groups]

    finally:
        # closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
            return observers

def fetchAccessPointsInfo():
    print("Starting to fetch access points information")
    connection = None
    try:
        connection = psycopg2.connect(
            user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT, database=DATABASE_NAME)
        cursor = connection.cursor()
        postgreSQL_select_Query = "SELECT * FROM edificios;"
        cursor.execute(postgreSQL_select_Query)
        allData = cursor.fetchall()
        seq = allData

        groups = groupby(seq, lambda x: x[0])
        aps = [[item[:] for item in data] for (key, data) in groups]

    finally:
        # closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
            return aps

def other():
    connection = None
    try:
        connection = psycopg2.connect(
            user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT, database=DATABASE_NAME)
        cursor = connection.cursor()
        postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenTime' as time,json_array_length(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM pruebasdiciembre ORDER BY mac,time) as res WHERE res.mac='F81F32F89FB4';"

        cursor.execute(postgreSQL_select_Query)
        print("Doing select time, mac and observers")
        mobile_records = cursor.fetchall()

        df = pd.DataFrame(data=mobile_records, columns=[
                          'mac', 'time', 'observers'])

        df['time'] = pd.to_datetime(df['time'])
        df.index = df['time']
        df_g = df.groupby(pd.Grouper(freq='1Min')).aggregate(np.sum)
        print(type(df_g))
        for dddd in df_g:
            print(dddd)

    finally:
        # closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
