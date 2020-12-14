import psycopg2
import math
from rssi import RSSI_Localizer
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import itertools
import datetime
from pytz import timezone
import openpyxl

EPSILON = 0.000001


def convert_to_AP(attenuation, x, y, distance, signal, name):
    accessPoint = {
        'signalAttenuation': attenuation,
        'location': {
            'y': y,
            'x': x
        },
        'reference': {
            'distance': distance,
            'signal': signal
        },
        'name': name
    }
    return accessPoint


class access_point:
    def __init__(self, mac, observers, seen_time, x, y, rssi):
        self.mac = mac
        self.observers = observers
        self.seen_time = seen_time
        self.x = x
        self.y = y
        self.rssi = rssi


def calculate_intersections(x0, y0, r0, x1,  y1, r1):

    intersections = []

    distance_x = x1 - x0
    distance_y = y1 - y0

    d = math.sqrt((distance_y * distance_y) + (distance_x * distance_x))
    if (d > (r0 + r1)):
        return None
    if (d < abs(r0 - r1)):
        return None
    a = ((r0 * r0) - (r1 * r1) + (d * d)) / (2.0 * d)

    point2_x = x0 + (distance_x * a / d)
    point2_y = y0 + (distance_y * a / d)

    h = math.sqrt((r0 * r0) - (a * a))

    rx = -distance_y * (h / d)
    ry = distance_x * (h / d)

    intersectionPoint1_x = point2_x + rx
    intersectionPoint2_x = point2_x - rx
    intersectionPoint1_y = point2_y + ry
    intersectionPoint2_y = point2_y - ry

    intersections.append(intersectionPoint1_x)
    intersections.append(intersectionPoint2_x)
    intersections.append(intersectionPoint1_y)
    intersections.append(intersectionPoint2_y)
    return intersections


def trilateration(x0, y0, r0, x1,  y1, r1, x2, y2, r2):
    dx = x1 - x0
    dy = y1 - y0

    intersectionsAP12 = calculate_intersections(x0, y0, r0, x1, y1, r1)
    # Determine the absolute intersection points.

    if(intersectionsAP12 != None):
        print("INTERSECTION AP1 AND AP2:" + "(" + str(intersectionsAP12[0]) + "," + str(intersectionsAP12[2]) + ")"
              + " AND (" + str(intersectionsAP12[1]) + "," + str(intersectionsAP12[3]) + ")")
    intersectionsAP13 = calculate_intersections(x0, y0, r0, x2, y2, r2)
    if(intersectionsAP13 != None):
        print("INTERSECTION AP1 AND AP3:" + "(" + str(intersectionsAP13[0]) + "," + str(intersectionsAP13[2]) + ")"
              + " AND (" + str(intersectionsAP13[1]) + "," + str(intersectionsAP13[3]) + ")")

    intersectionsAP23 = calculate_intersections(x1, y1, r1, x2, y2, r2)
    if(intersectionsAP23 != None):
        print("INTERSECTION AP2 AND AP3:" + "(" + str(intersectionsAP23[0]) + "," + str(intersectionsAP23[2]) + ")"
              + " AND (" + str(intersectionsAP23[1]) + "," + str(intersectionsAP23[3]) + ")")

    if(intersectionsAP12 != None):
        intersectionPoint1_x = intersectionsAP12[0]
        intersectionPoint2_x = intersectionsAP12[1]
        intersectionPoint1_y = intersectionsAP12[2]
        intersectionPoint2_y = intersectionsAP12[3]
        dx = intersectionPoint1_x - x2
        dy = intersectionPoint1_y - y2
        d1 = math.sqrt((dy * dy) + (dx * dx))

        dx = intersectionPoint2_x - x2
        dy = intersectionPoint2_y - y2
        d2 = math.sqrt((dy * dy) + (dx * dx))

        if (abs(d1 - r2) < EPSILON):
            print("INTERSECTION AP1 AND AP2 AND AP3:" + "(" + intersectionPoint1_x + ","
                  + intersectionPoint1_y + ")")
            return [intersectionPoint1_x, intersectionPoint1_y]
        elif (abs(d2 - r2) < EPSILON):
            print("INTERSECTION AP1 AND AP2 AND AP3:" + "(" + intersectionPoint2_x + ","
                  + intersectionPoint2_y + ")")
            return [intersectionPoint2_x, intersectionPoint2_y]
            # here was an error
        else:
            print("INTERSECTION AP1 AND AP2 AND AP3:" + " NONE")
    else:
        print("INTERSECTION AP1 AND AP2 AND AP3:" + " NONE")


def trilateration2(APS):
    intersectionsList = []
    apsNames = []
    for AP in APS:
        apsNames.append(AP['apName'])
    for AP1, AP2 in itertools.combinations(APS, 2):
        print(AP1, AP2)
        intersections = calculate_intersections(
            float(AP1['x']), float(AP1['y']), float(AP1['distance']),
            float(AP2['x']), float(AP2['y']), float(AP2['distance']))
        print(intersections)
        if intersections != None:
            print("INTERSECTION " + AP1['apName'] + " AND " + AP2['apName'] + "(" + str(intersections[0]) + ", " + str(intersections[2]) + ")"
                  + " AND (" + str(intersections[1]) + "," + str(intersections[3]) + ")")
            intersectionsList.append(intersections)
    return intersectionsList


try:
    connection = psycopg2.connect(user="postgres",
                                  password="firewall990612",
                                  host="127.0.0.1",
                                  port="5433",
                                  database="PDGAccessPointsDB")
    cursor = connection.cursor()
    postgreSQL_select_Query = """SELECT o.id,
	o.data->>'seenTime',
	o.data->>'clientMac',
	jsonb_array_length(o.data->'deviceObservers') as "Observers",
    JSON_AGG(
        JSON_BUILD_OBJECT('apLocation',
						  u."Location", 'name', u."Host Name",'mac', e.observers->'apMac', 'rssi',e.observers->'rssi',
                          'x',r.x,'y',R.y,'lat',r.lat,'lng',r.lng)
    )
    FROM apsfiles o
    INNER JOIN LATERAL JSONB_ARRAY_ELEMENTS(o.data->'deviceObservers') AS e(observers) ON TRUE
    INNER JOIN apsinfo u ON (e.observers->>'apMac')::text = u."MAC"
    INNER JOIN apscoordinates r ON (u."Host Name")::text = r."NOMBRE"
    WHERE o.data->>'clientMac'='F81F32F8A5D4'
    AND jsonb_array_length(o.data->'deviceObservers')::text::int>=3
    GROUP BY o.id
    ORDER BY o.data->>'seenTime'"""

    cursor.execute(postgreSQL_select_Query)
    print("Selecting rows from apinfo table using cursor.fetchall")
    aps_records = cursor.fetchall()

    cursor2 = connection.cursor()
    postgreSQL_select_Query2 = """SELECT o.id,  
	o.data->>'seenTime',
	o.data->>'clientMac',
	o.data->>'lat',
	o.data->>'lng',
	r."NOMBRE"
    FROM apsfiles o
    INNER JOIN apscoordinates r ON (o.data->>'lat')::text = r.lat::text
    WHERE o.data->>'clientMac'='F81F32F89FB4'
    GROUP BY o.id,r."NOMBRE"
    ORDER BY o.data->>'seenTime'"""

    cursor2.execute(postgreSQL_select_Query2)
    aps_latlng = cursor2.fetchall()

    cursor3 = connection.cursor()
    postgreSQL_select_Query3 = """SELECT o.id,  
	o.data->>'seenTime',
	o.data->>'clientMac',
	o.data->>'lat',
	o.data->>'lng',
	o.data->>'x',
	o.data->>'y',
	jsonb_array_length(o.data->'deviceObservers') as "Observers",
    JSON_AGG(
        JSON_BUILD_OBJECT('apLocation',
						  u."Location", 'name', u."Host Name",'mac', e.observers->'apMac', 'rssi',e.observers->'rssi')
    )
    FROM apsfiles o
    INNER JOIN LATERAL JSONB_ARRAY_ELEMENTS(o.data->'deviceObservers') AS e(observers) ON TRUE
    INNER JOIN apsinfo u ON (e.observers->>'apMac')::text = u."MAC"
    WHERE o.data->>'clientMac'='F81F32F8A5D4'
    AND u."Host Name"='AP-E04-P4-E-05'
    AND substring(o.data->>'seenTime',12,16)>='20:37'
    AND substring(o.data->>'seenTime',12,16)<='21:01'
    GROUP BY o.id
    ORDER BY o.data->>'seenTime'"""

    cursor3.execute(postgreSQL_select_Query3)
    aps_rssi = cursor3.fetchall()
    print("Print each row and it's columns values")

#  for row in aps_records:
#         if(row[1] == 4 or row[1] == 3):
#             print("MAC = ", row[0])
#             print("Observers = ", row[1])
#             print("Seen Time  = ", row[2], "\n")
#             print(row[3])
#             print(row[4])
#             print(row[5])
#             print(row[6])


except (Exception, psycopg2.Error) as error:
    print("Error while fetching data from PostgreSQL", error)

finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")


def calculateDistance(rssi):

    txPower = -59  # hard coded power value. Usually ranges between -59 to -65

    if (rssi == 0):
        return -1.0

    ratio = rssi*1.0/txPower
    if (ratio < 1.0):
        return math.pow(ratio, 10)
    else:
        distance = (0.89976)*math.pow(ratio, 7.7095) + 0.111
        return distance


def drawTrilateration(x0, y0, r0, x1,  y1, r1, x2, y2, r2):

    fig, ax = plt.subplots()
    ax.add_patch(plt.Circle((x0, y0), r0, color='r', alpha=0.5))
    ax.add_patch(plt.Circle((x1, y1), r1, color='#00ffff', alpha=0.5))
    ax.add_artist(plt.Circle((x2, y2), r2, color='#000033', alpha=0.5))

    ax.annotate("AP1", xy=(x0, y0), fontsize=10)
    ax.annotate("AP2", xy=(x1, y1), fontsize=10)
    ax.annotate("AP3", xy=(x2, y2), fontsize=10)

    intersections = calculate_intersections(x0, y0, r0, x1, y1, r1)
    if(intersections != None):

        plt.plot([intersections[0], intersections[1]], [
                 intersections[2], intersections[3]], '.', color='r')

    intersections = calculate_intersections(x0, y0, r0, x2, y2, r2)
    if(intersections != None):
        plt.plot([intersections[0], intersections[1]], [
                 intersections[2], intersections[3]], '.', color='r')

    intersections = calculate_intersections(x1, y1, r1, x2, y2, r2)
    if(intersections != None):
        plt.plot([intersections[0], intersections[1]], [
                 intersections[2], intersections[3]], '.', color='r')

    ax.set_aspect('equal', adjustable='datalim')
    ax.plot()
    plt.show()


def showLatLong():
    aps = []
    for ap in aps_latlng:
        date_time_obj = datetime.datetime.strptime(
            ap[1], '%Y-%m-%dT%H:%M:%S.%fZ')
        basedate = ap[1]
        formatfrom = "%Y-%m-%dT%H:%M:%S.%fZ"
        formatto = "%a %d %b %Y, %H:%M:%S GMT-5"

        east = timezone('UTC')
        colombia = timezone('America/Bogota')
        loc_dt = east.localize(datetime.datetime.strptime(
            basedate, formatfrom))
        a = (loc_dt.astimezone(colombia).strftime(
            formatto), ap[2], ap[3], ap[4], ap[5])
        aps.append(a)

    wb = openpyxl.Workbook()
    hoja = wb.active
    # Crea la fila del encabezado con los títulos
    hoja.append(('Tiempo', 'MAC', 'Lat', 'Long', 'AP Cercano'))
    for ap in aps:
        # producto es una tupla con los valores de un producto
        hoja.append(ap)
    wb.save('device1.xlsx')


def calculateRssiReference():
    aps = []
    for ap in aps_rssi:
        date_time_obj = datetime.datetime.strptime(
            ap[1], '%Y-%m-%dT%H:%M:%S.%fZ')
        basedate = ap[1]
        formatfrom = "%Y-%m-%dT%H:%M:%S.%fZ"
        formatto = "%a %d %b %Y, %H:%M:%S GMT-5"

        east = timezone('UTC')
        colombia = timezone('America/Bogota')
        loc_dt = east.localize(datetime.datetime.strptime(
            basedate, formatfrom))
        a = (loc_dt.astimezone(colombia).strftime(
            formatto), ap[2], ap[8][0]['rssi'])
        aps.append(a)

    wb = openpyxl.Workbook()
    hoja = wb.active
    # Crea la fila del encabezado con los títulos
    hoja.append(('Tiempo', 'MAC', 'rssi'))
    for ap in aps:
        # producto es una tupla con los valores de un producto
        hoja.append(ap)
    wb.save('rssi5.xlsx')


def drawTrilateration2(APS, intersections, time):

    fig, ax = plt.subplots()
    for AP in APS:
        ax.add_patch(plt.Circle((AP['x'], AP['y']),
                                AP['distance'], color='r', alpha=0.5))
        ax.annotate(AP['apName'], xy=(AP['x'], AP['y']), fontsize=10)

    for i in intersections:
        plt.plot([i[0], i[1]], [
                 i[2], i[3]], '.', color='#000000')

    ax.set_aspect('equal', adjustable='datalim')
    ax.plot()
    ax.set_title(time)
    plt.show()


def trilateration_all():

    for row in aps_records:
        # EXAMPLE PAPER
        coords = np.random.rand(int(row[3]), 2) * 5

        accessPoints = []

        # accessPoints = [convert_to_AP(1, coords[0, 0], coords[0, 1], 1, -50, 'AP-INFO1'),
        #                 convert_to_AP(1, coords[1, 0],
        #                               coords[1, 1], 1, -50, 'AP-INFO2'),
        #                 convert_to_AP(1, coords[2, 0], coords[2, 1], 1, -50, 'AP-INFO3')]
        signalStrengths = []
        i = 0
        names = []
        for ap in row[4]:
            accessPoints.append(convert_to_AP(
                1, ap['x'], ap['y'], 1, -80, ap['name']))
            i = i+1
            signalStrengths.append(ap['rssi'])
            names.append(ap['name'])

        rssi_localizer_instance = RSSI_Localizer(accessPoints=accessPoints)

        distances = rssi_localizer_instance.getDistancesForAllAPs(
            signalStrengths)
        for d in distances:
            d['apName'] = names[distances.index(d)]

        # distance = rssi_localizer_instance.getDistanceFromAP(
        #     accessPoints[0], signalStrength)
        # print(distances)

        # AP1 = access_point('DDDDDADAS', 4, 12,
        #                    float(distances[0]["x"]), float(distances[0]["y"]), float(distances[0]["distance"]))
        # AP2 = access_point('DDDDDADAS', 4, 12,
        #                    float(distances[1]["x"]), float(distances[1]["y"]), float(distances[1]["distance"]))
        # AP3 = access_point('DDDDDADAS', 4, 12,
        #                    float(distances[2]["x"]), float(distances[2]["y"]), float(distances[2]["distance"]))

        date_time_obj = datetime.datetime.strptime(
            row[1], '%Y-%m-%dT%H:%M:%S.%fZ')
        basedate = row[1]
        formatfrom = "%Y-%m-%dT%H:%M:%S.%fZ"
        formatto = "%a %d %b %Y, %H:%M:%S GMT-5"

        east = timezone('UTC')
        colombia = timezone('America/Bogota')
        loc_dt = east.localize(datetime.datetime.strptime(
            basedate, formatfrom))

        print(loc_dt.astimezone(colombia).strftime(formatto))
        # trilateration(AP1.x, AP1.y, AP1.rssi, AP2.x,
        #               AP2.y, AP2.rssi, AP3.x, AP3.y, AP3.rssi)
        # drawTrilateration(AP1.x, AP1.y, AP1.rssi, AP2.x,
        #                   AP2.y, AP2.rssi, AP3.x, AP3.y, AP3.rssi)

       # if loc_dt.astimezone(colombia).strftime(formatto) >= "Sat 31 Oct 2020, 13:55:12 GMT-5":
        intersections = trilateration2(distances)
        if len(intersections) > 0:
            drawTrilateration2(distances, intersections,
                               loc_dt.astimezone(colombia).strftime(formatto))


trilateration_all()
# calculateRssiReference()
# showLatLong()
