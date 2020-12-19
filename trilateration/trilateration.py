
import datetime
from pytz import timezone
import xlsxwriter
import math
import matplotlib.pyplot as plt
import openpyxl
import itertools

resultsComparisson = []

def handleAPMacInfo(accessPointInfo):
    return {
        "apName": accessPointInfo[1],
        "mac": accessPointInfo[2]
    }

def handleAPInfo(accessPoint):
    return {
        "piso": accessPoint[1],
        "nombre":  accessPoint[2],
        "edificio":  accessPoint[3],
        "x":  accessPoint[4],
        "y":  accessPoint[5],
        "lat":  accessPoint[6],
        "long":  accessPoint[7]
    }

def handleObserversInfo(observer):
    return {
        "mac": observer[0],
        "seentime":  observer[1],
        "rssi":  observer[2],
        "seenepoch":  observer[3],
        "apMac":  observer[4],
        "seentimeParsed": parseSeenTime(observer[1]),
    }

def parseSeenTime(seentime):
    formatfrom = "%Y-%m-%dT%H:%M:%S.%fZ"
    formatto = "%a %d %b %Y, %H:%M:%S GMT-5"
    east = timezone('UTC')
    colombia = timezone('America/Bogota')
    loc_dt = east.localize(datetime.datetime.strptime(seentime, formatfrom))
    datetime2 = loc_dt.astimezone(colombia).strftime(formatto)
    return datetime2

def saveAccessPointsInfo(aps):
  accessPoints = []
  for element in aps:
    for ap in element:
      accessPoints.append(handleAPInfo(ap))
  return accessPoints

def saveObserversInfo(observers):
  observersList = []
  for element in observers:
    for observer in element:
      observersList.append(handleObserversInfo(observer))
  return observersList

def distanceRealFromDevice(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

def handleTimeRange(observers, deviceMac):
    momentsProfile = []
    moments = []

    for observer in observers:
        observer.get('seentime')
        if observer.get('seentime') not in moments:
            moments.append(observer.get('seentime'))
            momentsProfile.append(momentProfile(observer.get('seentime')))
        else:
            increaseObserverNumber(momentsProfile, observer.get('seentime'))

    recordSeenTimes(momentsProfile, deviceMac)
    return momentsProfile

def recordSeenTimes(momentsProfile, deviceMac):
    workbook = xlsxwriter.Workbook('Seentimes-'+deviceMac+'.xlsx')
    worksheet = workbook.add_worksheet()

    row = 0
    for moment in momentsProfile:
        worksheet.write(row, 0, moment.get('seentime'))
        worksheet.write(row, 1, moment.get('observers_number'))
        row += 1
    worksheet.write(row, 0, 'Total number of observations')
    last_row = len(momentsProfile)
    worksheet.write(row, 1, '=SUM(B1:B'+str(last_row)+')')
    workbook.close()


def increaseObserverNumber(momentsProfile, seentime):
    obs = {}
    for x in momentsProfile:
        if x.get('seentime') == seentime:
            obs = x
            break;
    obs["observers_number"]+=1

def momentProfile(seentime):
    return {
        "seentime": seentime,
        "observers_number":  1,
    }

def observerApProfile(observer, ap):
    return {
        "apX": ap.get('x'),
        "apY": ap.get('y'),
        "distance": observer.get('distance'),
        "name": ap.get('nombre'),
        "seentime": observer.get('seentime')
    }

def trilat(device, momentsProfile, observers, accessPoints,apMacs,distanceMethod):
    deviceName = device
    for moment in momentsProfile:
        if moment.get('observers_number') > 2:
            executeTrilateration(deviceName,moment, observers, accessPoints,apMacs, distanceMethod)
    return resultsComparisson

def calculateddistanceLinealModel(observation):
    rssi = int(observation.get('rssi'))
    return -0.43887*rssi-21.4009

def calculateddistanceExponentialModel(observation):
    rssi = int(observation.get('rssi'))
    return 0.17927544*(math.e**(-0.04904022*rssi))

def getDistanceFromAP(observation, accessPoint):
    rssi = int(observation.get('rssi'))
    measuredPower = -52
    N = 4
    return pow(10, (measuredPower-rssi)/(10*N))

def getDistanceFromAP_ITU(observation, accessPoint):
    rssi = int(observation.get('rssi'))
    logF= 67.604224
    distance = (rssi - logF + 28) / 30 
    return distance

def findAccessPointByMac(apMac, accessPoints, apMacs):
    ap = ''
    for apInfo in apMacs:
        if apInfo.get('mac') == apMac:
            ap = apInfo
            break;
    if ap == '':
        print("Did not find any access point matching with mac: " + apMac)
    else:
        for a_p in accessPoints:
            if ap.get('apName') == a_p.get('nombre'):
                ap = a_p
    return ap
    ##for ap in accessPoints:
        ##print(ap.get("nombre"))
def accurateIntersection2(time, device, intersections, x, y):
  
    distances = []
    aps = []
    xCords = []
    yCords = []

    for i in intersections:
        xCords.append(i[0])
        yCords.append(i[1])
    
    index = 0

    for i in xCords:
        for j in yCords:
            distances.append(distanceRealFromDevice(
                i, j, x, y))

    minDistance = min(distances)

    print("min distances")
    print(minDistance)
    coords = distances.index(minDistance)
    print(coords)

    xCalculated = 0
    yCalculated = 0

    for i in xCords:
        for j in yCords:
            if coords == index:
                xCalculated = i
                yCalculated = j
            index = index +1

    errorx = abs(xCalculated - x)
    errory = abs(yCalculated - y)
    error2x = math.pow(errorx, 2)
    error2y = math.pow(errory, 2)

    a = (time, device, xCalculated, yCalculated, x, y, errorx, errory, error2x, error2y, minDistance)

    return a


def accurateIntersection(time, device, intersections, x, y):
    distances = []
    aps = []
    i = 0
  
    distances.append(distanceRealFromDevice(
            intersections[0], intersections[1], x, y))
    distances.append(distanceRealFromDevice(
            intersections[2], intersections[3], x, y))

    minDistance = min(distances)

    coords = distances.index(minDistance)
    if coords == 0:
      intX = intersections[0]
      intY = intersections[1]
    if coords == 1:
      intX = intersections[2]
      intY = intersections[3]
    errorx = abs(intX - x)
    errory = abs(intY - y)
    error2x = math.pow(errorx, 2)
    error2y = math.pow(errory, 2)

    a = (time, device, intX, intY, x, y, errorx, errory, error2x, error2y, minDistance)
    return a

def printResultsMethods(aps):
  
    wb = openpyxl.Workbook()
    hoja = wb.active
    # Crea la fila del encabezado con los títulos
    hoja.append(('Tiempo', 'Dispositivo', 'Intersection X', 'Intersection Y',
                 'Ubicacion X', 'Ubicacion Y', 'Error Absoluto X', 'Error Absoluto Y', 'Error Cuadrado X',
                 'Error Cuadrado Y', 'Distancia a ubicacion real'))
    for ap in aps:

        hoja.append(ap)
    wb.save('triangulacionLogD.xlsx')

def executeTrilateration(deviceName, moment, observers,accessPoints, apMacs, distanceMethod):
   foundAps = 0;
   observations = []
   intersectionsAll = []
   deviceObservers = []
   for observer in observers:
        if observer.get('seentime') == moment.get('seentime'):
            observations.append(observer)
   for obs in observations:
        accessPoint = findAccessPointByMac(obs.get('apMac'), accessPoints,apMacs)
        if distanceMethod == 1:
            obs["distance"] = getDistanceFromAP(obs, accessPoint)
        if distanceMethod == 2:
            obs["distance"] = getDistanceFromAP_ITU(obs, accessPoint)
        if distanceMethod == 3:
            obs["distance"] = calculateddistanceLinealModel(obs)
        if distanceMethod == 4:
            obs["distance"] = calculateddistanceExponentialModel(obs)

        if accessPoint != '':
            foundAps += 1
            deviceObservers.append(observerApProfile(obs, accessPoint))


   if foundAps < 3:
        print("This trilateration cannot be finished because Access point information is missing")
   else:
        intersections = drawTrilateration(deviceName, deviceObservers)
        for i in intersections:
            intersectionsAll.append(i)
   print(intersectionsAll)
   seentime = parseSeenTime(moment.get('seentime'))
   xExpected = expectedX(deviceName, seentime)
   yExpected = expectedY(deviceName, seentime)
   resultsComparisson.append(accurateIntersection2(seentime, deviceName, intersectionsAll, xExpected, yExpected))

def drawTrilateration(deviceName, deviceObservers):
    fig, ax = plt.subplots()

    intersections = []
    for do in deviceObservers:
         if do.get('name') != None:
            seentime = parseSeenTime(do.get('seentime'))

            ax.add_patch(plt.Circle((do.get('apX'), do.get('apY')), do.get('distance'), color='b', alpha=0.5))
            ax.annotate(do.get('name'), xy=(do.get('apX'), do.get('apY')), fontsize=10)
            for do1 in deviceObservers:
                if do1.get('name') != do.get('name') and do1.get('name') != None:
                    intersection = calculate_intersections(do1.get('apX'), do1.get('apY'), do1.get('distance'), do.get('apX'), do.get('apY'), do.get('distance'))
                    
                    if intersection != None:
                            firstIntersection = []
                            secondIntersection = []
                            firstIntersection.append(intersection[0])
                            firstIntersection.append(intersection[1])

                            secondIntersection.append(intersection[2])
                            secondIntersection.append(intersection[3])
                            intersections.append(secondIntersection)
                            intersections.append(firstIntersection)

                            plt.plot([intersection[0], intersection[1]], [
                            intersection[2], intersection[3]], '.', color='r')
    ##resultsComparisson.append(accurateIntersection2(seentime, deviceName, intersection, xExpected, yExpected))
    ax.set_aspect('equal', adjustable='datalim')
    ax.plot()
    ax.set_title(seentime)
    return intersections
    #plt.show()


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

#### HACER VARIOS METODOS

def expectedY(deviceName, seentime):
    hour = seentime.split(" ")[4]
    mins = hour.split(":")[1]
    hourH = hour.split(":")[0]

    if deviceName == "F81F32F89FB4":
        if int(mins) > 36:
            return 4.6333
        if int(mins) < 36 and int(mins) > 26:
            return 13.821
        if (int(mins) < 26 or int(mins)== 26) and (int(mins) > 21 or int(mins)==21):
            return 15.821
        if int(mins) == 10:
            return 12.821
        if int(mins) > 15 and int(mins) < 21:
            return 11.821
        else: 
            return 14.821
    if deviceName == "F81F32F8A5D4":
        if int(hourH) == 14 or (int(hourH) == 15 and int(mins) < 10):
            return 15.821
        if int(hourH) == 15 and (int(mins) > 10 or int(mins) < 43):
            return  4.633
        if int(hourH) == 15 and (int(mins)>42 or int(mins)< 49):
            return 3.633
        if (int(hourH) == 15 and int(mins) >48) or (int(hourH) == 16 and int(mins) < 3):
            return 3.016
        if int(hourH) == 16 and int(min) < 29:
            return -6.172
        else:
            return 10
    else:
        return 40

def expectedX(deviceName, seentime):
    hour = seentime.split(" ")[4]
    mins = hour.split(":")[1]
    hourH = hour.split(":")[0]

    if deviceName == "F81F32F89FB4":
        if int(mins) > 36:
            return 63.721
        else:
            return 70.522
    if deviceName == "F81F32F8A5D4":
        if int(hourH) == 14 or (int(hourH) == 15 and int(mins) < 10):
            return 70.522
        if int(hourH) == 15 and (int(mins) > 10):
            return  63.721
        else:
            return 10
    else:
        return 40
        