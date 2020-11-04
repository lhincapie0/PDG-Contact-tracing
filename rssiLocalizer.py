import psycopg2
import math
from rssi import RSSI_Localizer
import matplotlib.pyplot as plt
import numpy as np

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


try:
    connection = psycopg2.connect(user="postgres",
                                  password="firewall990612",
                                  host="127.0.0.1",
                                  port="5433",
                                  database="PDGAccessPointsDB")
    cursor = connection.cursor()
    postgreSQL_select_Query = "SELECT apsfiles.data ->>'clientMac' as MAC, jsonb_array_length(apsfiles.data -> 'deviceObservers') as Observers, CAST(apsfiles.data ->>'seenTime' AS TIMESTAMP) as SEENTIME, data -> 'deviceObservers' -> 0 ->>'apMac' as apmac1,data -> 'deviceObservers' -> 1 ->>'apMac' as apmac2,data -> 'deviceObservers' -> 2 ->>'apMac' as apmac3,data -> 'deviceObservers' -> 3 ->>'apMac' as apmac4 FROM apsfiles, jsonb_array_elements(data -> 'deviceObservers')  GROUP BY apsfiles.data ORDER BY apsfiles.data -> 'seenTime' "

    cursor.execute(postgreSQL_select_Query)
    print("Selecting rows from apinfo table using cursor.fetchall")
    aps_records = cursor.fetchall()

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


# EXAMPLE PAPER
coords = np.random.rand(3, 2) * 5
print(coords)


# AP1 = access_point('DDDDDADAS', 4, 12, 1.5, 1.5, 2.47)
# AP2 = access_point('DDDDDADAS', 4, 12, 4.5, 2, 2.86)
# AP3 = access_point('DDDDDADAS', 4, 12, 7.5, 2.5, 5.35)
accessPoints = [convert_to_AP(1, coords[0, 0], coords[0, 1], 1, -50, 'AP-INFO1'),
                convert_to_AP(1, coords[1, 0],
                              coords[1, 1], 1, -50, 'AP-INFO2'),
                convert_to_AP(1, coords[2, 0], coords[2, 1], 1, -50, 'AP-INFO3')]
rssi_localizer_instance = RSSI_Localizer(accessPoints=accessPoints)

signalStrength = -49

distances = rssi_localizer_instance.getDistancesForAllAPs(
    [-49, -53, -50])


distance = rssi_localizer_instance.getDistanceFromAP(
    accessPoints[0], signalStrength)
print(distances)

AP1 = access_point('DDDDDADAS', 4, 12,
                   coords[0, 0], coords[0, 1], float(distances[0]["distance"]))
AP2 = access_point('DDDDDADAS', 4, 12,
                   coords[1, 0], coords[1, 1], float(distances[1]["distance"]))
AP3 = access_point('DDDDDADAS', 4, 12,
                   coords[2, 0], coords[2, 1], float(distances[2]["distance"]))
# example with coordinates APinfo


trilateration(AP1.x, AP1.y, AP1.rssi, AP2.x,
              AP2.y, AP2.rssi, AP3.x, AP3.y, AP3.rssi)


def drawTrilateration(x0, y0, r0, x1,  y1, r1, x2, y2, r2):

    fig, ax = plt.subplots()
    ax.add_patch(plt.Circle((x0, y0), AP1.rssi, color='r', alpha=0.5))
    ax.add_patch(plt.Circle((x1, y1), AP2.rssi, color='#00ffff', alpha=0.5))
    ax.add_artist(plt.Circle((x2, y2), AP3.rssi, color='#000033', alpha=0.5))

    ax.annotate("AP1", xy=(x0, y0), fontsize=10)
    ax.annotate("AP2", xy=(x1, y1), fontsize=10)
    ax.annotate("AP3", xy=(x2, y2), fontsize=10)

    intersections = calculate_intersections(x0, y0, r0, x1, y1, r1)
    if(intersections != None):
        print(intersections)
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


drawTrilateration(AP1.x, AP1.y, AP1.rssi, AP2.x,
                  AP2.y, AP2.rssi, AP3.x, AP3.y, AP3.rssi)
