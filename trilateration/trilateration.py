
import datetime
from pytz import timezone
import xlsxwriter

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
    return loc_dt.astimezone(colombia).strftime(formatto)

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

def trilat(momentsProfile, observers, accessPoints,apMacs):
    for moment in momentsProfile:
        if moment.get('observers_number') > 2:
            executeTrilateration(moment, observers, accessPoints,apMacs)

def getDistanceFromAP(observation, accessPoint):
    print("hola")

def findAccessPointByMac(apMac, accessPoints, apMacs):
    ap = ''
    for apInfo in apMacs:
        if apInfo.get('mac') == apMac:
            ap = apInfo
            break;
    if ap == '':
        print("Did not find any access point matching with mac: " + apMac)
    return ap
    ##for ap in accessPoints:
        ##print(ap.get("nombre"))

def executeTrilateration(moment, observers,accessPoints, apMacs):
   foundAps = 0;
   observations = []
   for observer in observers:
        if observer.get('seentime') == moment.get('seentime'):
            observations.append(observer)
   for obs in observations:
        accessPoint = findAccessPointByMac(obs.get('apMac'), accessPoints,apMacs)
        if accessPoint != '':
            foundAps += 1

   if foundAps < 3:
        print("This trilateration cannot be finished because Access point information is missing")
   else:
        print("Calculating distances between AP and device")

