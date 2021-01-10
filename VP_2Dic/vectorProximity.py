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

# El siguiente script tiene como fin la definición y ejecución del algoritmo de vectores de proximidad definido en el documento de grado.
# Además, tiene los datos necesarios para la ejecución e impresión de pruebas para el día 2 de diciembre

# Valor minimo considerado para el RSSI, parámetro usado por el método de VP
LOW_RSSI = -100

# Clase de perfil de señal. Contiene la mac, tiempo y la lista de aps con sus rssi vistos por un dispositivo


class signal_profile_object:
    def __init__(self, mac, time):
        self.mac = mac
        self.time = time
        self.aps = []
        self.rssis = []

# Clase de perfil de señal continuo. Contiene la mac, rangos de tiempo y los aps con sus rssi vistos por un dispositivo en dicho rango de tiempo.


class continuous_profile_object:
    def __init__(self, mac, start_time, final_time, aps, rssis):
        self.mac = mac
        self.start_time = start_time
        self.final_time = final_time
        self.aps = aps
        self.rssis = rssis

# Metodo que carga el resultado del query a la base de datos a la clase de perfil de señal


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

# Metodo que crea un perfil de señal continuo a partir de la clase perfil de señal


def continuous_signal(signal_profile_input):
    signal_profile = signal_profile_input.copy()
    obj = signal_profile[len(signal_profile)-1]
    # Creación del último rango de tiempo.
    signal_profile.append(signal_profile_object(obj.mac, obj.time+60000))
    continuous_profile = []
    for i in range(len(signal_profile)-1):
        # Unión de los conjuntos de APs
        join_aps = list(set(signal_profile[i].aps + signal_profile[i+1].aps))
        join_rssis = []
        # Definición de los rangos validos de rssi para la unión de conjuntos de APs
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

# Método que calcula el valor de proximidad P a partir de un objeto de perfil de señal y un objeto de perfil de señal continuo(infectado)


def signal_proximity(continuous_object, signal_object):
    # Cantidad de dispositivos en común
    overlap = len([w for w in signal_object.aps if w in continuous_object.aps])
    # Valor O
    overlap_ratio = overlap / \
        min(len(continuous_object.aps), len(signal_object.aps))
    dif = 0
    # Calculo del valor D
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
    # Valor P
    return overlap_ratio/(avg_difference+1)

# Método que calcula el valor de proximidad para cada instante de tiempo que compartan dos perfiles de señal(uno continuo)


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

# Definición de errores y excepciones de la conexión a base de datos


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


# Instantes de tiempo para cada prueba realizada el día 2 de diciembre
tests = [
    ('Prueba 2', 1606938960000, 1606939380000),
    ('Prueba 4', 1606939380000, 1606939740000),
    ('Prueba 5', 1606939740000, 1606940100000),
    ('Prueba 6', 1606940100000, 1606940460000),
    ('Prueba 1', 1606940460000, 1606940820000),
    ('Prueba 3', 1606940820000, 1606941240000),
    ('Prueba 7_1', 1606941420000, 1606941780000),
    ('Prueba 8_1', 1606941780000, 1606942140000),
    ('Prueba 9_1', 1606942140000, 1606942500000),
    ('Prueba 10_1', 1606942560000, 1606942920000),
    ('Prueba 7_2', 1606943100000, 1606943460000),
    ('Prueba 8_2', 1606943460000, 1606943820000),
    ('Prueba 9_2', 1606943820000, 1606944120000),
    ('Prueba 10_2', 1606944120000, 1606944480000),
    ('Prueba 7_3', 1606944660000, 1606945020000),
    ('Prueba 8_3', 1606945020000, 1606945380000),
    ('Prueba 9_3', 1606945380000, 1606945680000),
    ('Prueba 10_3', 1606945680000, 1606946040000),
]

# Calculo de los valores P, desviación estandar y IOD para cada prueba


def testAverages(metrics, suspect, infected):
    ret = ()
    for test in tests:
        testValues = []
        for metric in metrics:
            if(metric[-1] < test[1]):
                continue
            elif(metric[-1] >= test[1] and metric[-1] < test[2]):
                # valueSum = valueSum+metric[0]
                # iterations = iterations+1
                testValues.append(metric[0])
            else:
                break
        if(len(testValues) == 0):
            ret1 = ('NP', 'NP', 'NP')
        else:
            average = sum(testValues)/len(testValues)
            stdev = np.std(testValues)
            iod = np.var(testValues)/(sum(testValues)/len(testValues))
            ret1 = (average, stdev, iod)
        ret = ret+ret1
    ret = (suspect, infected) + ret
    # print(ret)
    series = pd.Series(ret)
    return series


connection = None
try:
    # Conexión a la base de datos
    connection = psycopg2.connect(
        user="postgres", password="postgres", host="127.0.0.1", port="5432", database="pdgdata")
    cursor = connection.cursor()
    # Lista de direcciones MAC con las que se realizaron las pruebas
    macs_list = ['F81F32F89FB4', 'F81F32F8A61E', 'F81F32F8A5D4']
    # Definición de salida en Excel en caso de querer comparar cada par de dispositivos
    # writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
    df = pd.DataFrame()
    # Ciclos para realizar las pruebas de todos los elementos de la lista de MAC con todos los otros
    for mac_suspect in macs_list:
        for mac_infected in macs_list:
            if mac_suspect != mac_infected:
                # Consulta para traer los datos del perfil continuo(infectado)
                postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenEpoch' as time,(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM public.example2dic ORDER BY mac,time) as res WHERE res.mac='"+mac_infected+"';"
                cursor.execute(postgreSQL_select_Query)
                records = cursor.fetchall()
                infected_profile = signal_profile(records)
                infected_continuous = continuous_signal(infected_profile)
                # Consulta para traer los datos del perfil a comparar
                postgreSQL_select_Query = "SELECT * FROM(SELECT json_array_elements(data->'data'->'observations')->>'clientMac' as mac,json_array_elements(data->'data'->'observations')->>'seenEpoch' as time,(json_array_elements(data->'data'->'observations')->'deviceObservers') as observers FROM public.example2dic ORDER BY mac,time) as res WHERE res.mac='"+mac_suspect+"';"
                cursor.execute(postgreSQL_select_Query)
                records = cursor.fetchall()
                suspect_profile = signal_profile(records)
                # Calculo de metricas de resultados
                metrics = signal_metrics(infected_continuous, suspect_profile)
                print('Analisis para: '+mac_infected+' con: '+mac_suspect)
                series = testAverages(metrics, mac_suspect, mac_infected)
                df = df.append(series, ignore_index=True)
                # Guardar el resultado de cada par de pruebas en una tabla de excel
                # create DataFrame using data
                # df = pd.DataFrame(metrics, columns=[
                #                   'Proximity', 'StartT', 'EndT', 'MeasuredT'])
                # df.to_excel(writer, mac_infected+'_'+mac_suspect)
    # writer.save()
    df.to_excel('test.xlsx')
    print(df)

finally:
    # Cerrar conexión a base de datos
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
