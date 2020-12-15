
import datetime
from pytz import timezone

def handleAPInfo(accessPoint):
    return {
        "piso": accessPoint[1],
        "nombre":  accessPoint[2],
        "edificio":  accessPoint[2],
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
        "apName":  observer[3],
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

def handleTimeRange(observers):
    momentsProfile = []
    moments = []


    for observer in observers:
        observer.get('seentime')
        if observer.get('seentime') not in moments:
            moments.append(observer.get('seentime'))
            momentsProfile.append(momentProfile(observer.get('seentime')))
        else:
            increaseObserverNumber(momentsProfile, observer.get('seentime'))

    for mom in momentsProfile:
       print(mom)

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

