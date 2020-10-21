import psycopg2
import math
from rssi import RSSI_Localizer

EPSILON = 0.000001
accessPoint = {
    'signalAttenuation': 3,
    'location': {
        'y': 74,
        'x': 231
    },
    'reference': {
        'distance': 4,
        'signal': -50
    },
    'name': 'dd-wrt'
}
rssi_localizer_instance = RSSI_Localizer(accessPoints=accessPoint)

signalStrength = -99

distance = rssi_localizer_instance.getDistanceFromAP(
    accessPoint, signalStrength)


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
    intersectionPoint1_x = intersectionsAP12[0]
    intersectionPoint2_x = intersectionsAP12[1]
    intersectionPoint1_y = intersectionsAP12[2]
    intersectionPoint2_y = intersectionsAP12[3]

    print("INTERSECTION AP1 AND AP2:" + "(" + str(intersectionPoint1_x) + "," + str(intersectionPoint1_y) + ")"
          + " AND (" + str(intersectionPoint2_x) + "," + str(intersectionPoint2_y) + ")")
    intersectionsAP13 = calculate_intersections(x0, y0, r0, x2, y2, r2)

    print("INTERSECTION AP1 AND AP3:" + "(" + str(intersectionsAP13[0]) + "," + str(intersectionsAP13[2]) + ")"
          + " AND (" + str(intersectionsAP13[1]) + "," + str(intersectionsAP13[3]) + ")")

    intersectionsAP23 = calculate_intersections(x1, y1, r1, x2, y2, r2)

    print("INTERSECTION AP2 AND AP3:" + "(" + str(intersectionsAP23[0]) + "," + str(intersectionsAP23[2]) + ")"
          + " AND (" + str(intersectionsAP23[1]) + "," + str(intersectionsAP23[3]) + ")")

    dx = intersectionPoint1_x - x2
    dy = intersectionPoint1_y - y2
    d1 = math.sqrt((dy * dy) + (dx * dx))

    dx = intersectionPoint2_x - x2
    dy = intersectionPoint2_y - y2
    d2 = math.sqrt((dy * dy) + (dx * dx))

    if (abs(d1 - r2) < EPSILON):
        print("INTERSECTION AP1 AND AP2 AND AP3:" + "(" + intersectionPoint1_x + ","
              + intersectionPoint1_y + ")")
    elif (abs(d2 - r2) < EPSILON):
        print("INTERSECTION AP1 AND AP2 AND AP3:" + "(" + intersectionPoint2_x + ","
              + intersectionPoint2_y + ")")
        # here was an error
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
print(distance)

# example with coordinates APinfo
print(trilateration(12.92732259, -27.85846534, 3.0,
                    11.32153227, -27.83017898, 2.0,
                    4.149949553, -26.74243983, 8.0))
