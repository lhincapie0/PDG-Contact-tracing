import numpy as np
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import sys
import datetime
from psycopg2 import connect
from psycopg2 import OperationalError, errorcodes, errors
from itertools import groupby
from operator import itemgetter
import os

AVERAGE_POTENCE = 70
LOW_RSSI = -100


class signal_profile_object:
    def __init__(self, mac, time):
        self.mac = mac
        self.time = time
        self.aps = []
        self.rssis = []


class continuous_profile_object:
    def __init__(self, mac, start_time, final_time, aps, rssis):
        self.mac = mac
        self.start_time = start_time
        self.final_time = final_time
        self.aps = aps
        self.rssis = rssis


def signal_profile(records):
    profile = []
    for record in records:
        po = signal_profile_object(record[0], int(record[1]))
        aps = []
        rssis = []
        for ap in record[2]:
            aps.append(ap['apMac'])
            rssis.append(int(ap['rssi']))
        po.aps = aps
        po.rssis = rssis
        profile.append(po)
    return profile


def continuous_signal(signal_profile_input):
    signal_profile = signal_profile_input.copy()
    obj = signal_profile[len(signal_profile)-1]
    signal_profile.append(signal_profile_object(obj.mac, obj.time+60000))
    continuous_profile = []
    for i in range(len(signal_profile)-1):
        join_aps = list(set(signal_profile[i].aps + signal_profile[i+1].aps))
        join_rssis = []
        for ap in join_aps:
            try:
                index1 = signal_profile[i].aps.index(ap)
            except ValueError:
                index1 = -1
            try:
                index2 = signal_profile[i+1].aps.index(ap)
            except ValueError:
                index2 = -1
            if(index1 == -1):
                join_rssis.append(
                    (LOW_RSSI, signal_profile[i+1].rssis[index2]))
            elif(index2 == -1):
                join_rssis.append((LOW_RSSI, signal_profile[i].rssis[index1]))
            else:
                join_rssis.append((min(signal_profile[i+1].rssis[index2], signal_profile[i].rssis[index1]), max(
                    signal_profile[i+1].rssis[index2], signal_profile[i].rssis[index1])))

        continuous_profile.append(continuous_profile_object(
            signal_profile[i].mac, signal_profile[i].time, signal_profile[i+1].time, join_aps, join_rssis))
    return continuous_profile


def signal_proximity(continuous_object, signal_object):
    overlap = len([w for w in signal_object.aps if w in continuous_object.aps])
    overlap_ratio = overlap / \
        min(len(continuous_object.aps), len(signal_object.aps))
    dif = 0
    for i in range(len(signal_object.aps)):
        difference = 0
        try:
            index = continuous_object.aps.index(signal_object.aps[i])
            value = signal_object.rssis[i]
            minvalue = continuous_object.rssis[index][0]
            maxvalue = continuous_object.rssis[index][1]
            if value < minvalue:
                difference = minvalue-value
            elif value > maxvalue:
                difference = value-maxvalue
            difference = abs(difference)
        except ValueError:
            pass
        dif = dif+difference
    if(overlap == 0):
        return 0
    avg_difference = dif/overlap
    return overlap_ratio/(avg_difference+1)


def signal_metrics(infected_continuous, subject_profile):
    if os.path.exists("compare.txt"):
        os.remove("compare.txt")
    file1 = open("compare.txt", "a")
    index = 0
    metrics = []
    for i in range(len(subject_profile)):
        while(index < len(infected_continuous)):
            if subject_profile[i].time < infected_continuous[0].start_time:
                break
            if subject_profile[i].time >= infected_continuous[index].start_time and subject_profile[i].time < infected_continuous[index].final_time:
                metrics.append((signal_proximity(
                    infected_continuous[index], subject_profile[i]), infected_continuous[index].start_time, infected_continuous[index].final_time, subject_profile[i].time))
                file1.write(
                    str(metrics[-1][0])+'-'+str(metrics[-1][1])+'-'+str(metrics[-1][2])+str(metrics[-1][3])+'\n')
                break
            else:
                index = index+1
    file1.close()
    return metrics


def print_psycopg2_exception(err):
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()
    # get the line number when exception occured
    line_num = traceback.tb_lineno
    print("\npsycopg2 ERROR:", err, "on line number:", line_num)
    print("psycopg2 traceback:", traceback, "-- type:", err_type)
    # psycopg2 extensions.Diagnostics object attribute
    print("\nextensions.Diagnostics:", err.diag)
    # print the pgcode and pgerror exceptions
    print("pgerror:", err.pgerror)
    print("pgcode:", err.pgcode, "\n")


tests = [('Test1', 1604170740000, 1604171760000),
         ('Test2', 1604171820000, 1604172780000),
         ('Test3', 1604172840000, 1604173800000),
         ('Test4', 1604173920000, 1604174340000),
         ('Test7_1', 1604174400000, 1604174700000),
         ('Test7_2', 1604174700000, 1604174940000),
         ('Test7_3', 1604174940000, 1604175180000),
         ('Test9_1', 1604175240000, 1604175480000),
         ('Test9_2', 1604175480000, 1604175720000),
         ('Test9_3', 1604175720000, 1604175960000)
         ]


def testAverages(metrics):
    for test in tests:
        valueSum = 0
        iterations = 0
        for metric in metrics:
            if(metric[-1] < test[1]):
                continue
            elif(metric[-1] >= test[1] and metric[-1] < test[2]):
                valueSum = valueSum+metric[0]
                iterations = iterations+1
            else:
                break
        if(iterations == 0):
            print(test[0]+' not performed')
        else:
            print(test[0]+' Average:'+str(valueSum/iterations))


connection = None
try:
    connection = psycopg2.connect(
        user="postgres", password="postgres", host="127.0.0.1", port="5432", database="pdgdata")
    cursor = connection.cursor()
    # postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenEpoch' as time,(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM public.example ORDER BY mac,time) as res;"
    # cursor.execute(postgreSQL_select_Query)
    # allData = cursor.fetchall()
    # seq = allData
    # #seq.sort(key = lambda x: x[0])
    # groups = groupby(seq, lambda x: x[0])
    # new_list = [[item[:] for item in data] for (key, data) in groups]
    # for element in new_list:
    #     suceptible_profile = signal_profile(element)
    #     metrics = signal_metrics(infected_continuous, suceptible_profile)
    #     print('Analisis para: '+str(element[0][0]))
    #     print(metrics)
    macs_list = ['60AB67B94E5D', '8035C14D35F4', '58E6BA7C10E8',
                 '8875989F746A', '34F64B76676D', '2446C8A8C839']
    #writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
    for mac_suspect in macs_list:
        for mac_infected in macs_list:
            if mac_suspect != mac_infected:
                postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenEpoch' as time,(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM public.example ORDER BY mac,time) as res WHERE res.mac='"+mac_infected+"';"
                cursor.execute(postgreSQL_select_Query)
                records = cursor.fetchall()
                infected_profile = signal_profile(records)
                infected_continuous = continuous_signal(infected_profile)
                postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenEpoch' as time,(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM public.example ORDER BY mac,time) as res WHERE res.mac='"+mac_suspect+"';"
                cursor.execute(postgreSQL_select_Query)
                records = cursor.fetchall()
                suspect_profile = signal_profile(records)
                metrics = signal_metrics(infected_continuous, suspect_profile)
                print('Analisis para: '+mac_infected+' con: '+mac_suspect)
                testAverages(metrics)
                # create DataFrame using data
                # df = pd.DataFrame(metrics, columns=[
                #                   'Proximity', 'StartT', 'EndT', 'MeasuredT'])
                #df.to_excel(writer, mac_infected+'_'+mac_suspect)
    # writer.save()

finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
